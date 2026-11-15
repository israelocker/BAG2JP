// Process-only WASAPI collector. ABI verified against Windows SDK 10.0.26100.0.
// No default endpoint, microphone, EXCLUDE mode, or fallback exists in this helper.
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace Bag2ProcessAudio
{
    [StructLayout(LayoutKind.Sequential)]
    struct ActivationParams { public uint Type, TargetPid, Mode; }
    [StructLayout(LayoutKind.Sequential)]
    struct Blob { public uint Bytes; public IntPtr Data; }
    [StructLayout(LayoutKind.Sequential)]
    struct PropVariant { public ushort Type, Reserved1, Reserved2, Reserved3; public Blob Blob; }
    [StructLayout(LayoutKind.Sequential, Pack = 2)]
    struct WaveFormat
    {
        public ushort Tag, Channels;
        public uint Rate, BytesPerSecond;
        public ushort Align, Bits, Extra;
    }
    [ComImport, Guid("72A22D78-CDE4-431D-B8CC-843A71199B6D"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    public interface IActivationOperation
    {
        [PreserveSig] int GetActivateResult(out int result, [MarshalAs(UnmanagedType.IUnknown)] out object activated);
    }
    [ComImport, Guid("1CB9AD4C-DBFA-4C32-B178-C2F568A703B2"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IAudioClient
    {
        [PreserveSig] int Initialize(uint mode, uint flags, long duration, long periodicity, ref WaveFormat format, IntPtr session);
        [PreserveSig] int GetBufferSize(out uint frames);
        [PreserveSig] int GetStreamLatency(out long latency);
        [PreserveSig] int GetCurrentPadding(out uint frames);
        [PreserveSig] int IsFormatSupported(uint mode, IntPtr format, out IntPtr closest);
        [PreserveSig] int GetMixFormat(out IntPtr format);
        [PreserveSig] int GetDevicePeriod(out long normal, out long minimum);
        [PreserveSig] int Start();
        [PreserveSig] int Stop();
        [PreserveSig] int Reset();
        [PreserveSig] int SetEventHandle(IntPtr handle);
        [PreserveSig] int GetService(ref Guid iid, [MarshalAs(UnmanagedType.IUnknown)] out object service);
    }
    [ComImport, Guid("C8ADBD64-E71E-48A0-A4DE-185C395CD317"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IAudioCaptureClient
    {
        [PreserveSig] int GetBuffer(out IntPtr data, out uint frames, out uint flags, out ulong position, out ulong qpc);
        [PreserveSig] int ReleaseBuffer(uint frames);
        [PreserveSig] int GetNextPacketSize(out uint frames);
    }
    [ComVisible(true), Guid("41D949AB-9862-444A-80F6-C261334DA5EB"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    public interface ICompletion
    {
        [PreserveSig] int ActivateCompleted([MarshalAs(UnmanagedType.Interface)] IActivationOperation operation);
    }
    [ComVisible(true), Guid("94EA2B94-E9CC-49E0-C0FF-EE64CA8F5B90"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    public interface IAgile { }
    [ComVisible(true), ClassInterface(ClassInterfaceType.None)]
    public sealed class Completion : ICompletion, IAgile
    {
        internal readonly ManualResetEventSlim Done = new ManualResetEventSlim();
        internal int Result = unchecked((int)0x8000FFFF);
        internal object Activated;
        public int ActivateCompleted(IActivationOperation operation)
        {
            try
            {
                int callback = operation.GetActivateResult(out Result, out Activated);
                if (callback < 0) Result = callback;
            }
            // No managed exception may cross a COM callback boundary.
            catch (Exception error) { Result = Marshal.GetHRForException(error); }
            finally { Done.Set(); }
            return 0;
        }
    }

    sealed class ProcessLease : IDisposable
    {
        const uint QueryAndSynchronize = 0x00101000;
        readonly IntPtr handle;
        [DllImport("kernel32.dll", SetLastError = true)] static extern IntPtr OpenProcess(uint access, bool inherit, uint pid);
        [DllImport("kernel32.dll", SetLastError = true)] static extern bool CloseHandle(IntPtr value);
        [DllImport("kernel32.dll", SetLastError = true)] static extern bool GetProcessTimes(IntPtr value, out long created, out long exited, out long kernel, out long user);
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)] static extern bool QueryFullProcessImageName(IntPtr value, uint flags, StringBuilder path, ref uint size);
        [DllImport("kernel32.dll")] static extern uint WaitForSingleObject(IntPtr value, uint milliseconds);
        internal ProcessLease(JsonElement expected)
        {
            uint pid = expected.GetProperty("pid").GetUInt32();
            if (pid == 0) throw new InvalidDataException("PID zero is forbidden");
            handle = OpenProcess(QueryAndSynchronize, false, pid);
            if (handle == IntPtr.Zero) throw new Win32Exception(Marshal.GetLastWin32Error());
            try
            {
                long created, exited, kernel, user;
                uint size = 32768;
                var path = new StringBuilder((int)size);
                if (!GetProcessTimes(handle, out created, out exited, out kernel, out user) ||
                    !QueryFullProcessImageName(handle, 0, path, ref size))
                    throw new Win32Exception(Marshal.GetLastWin32Error());
                if (created.ToString(CultureInfo.InvariantCulture) != expected.GetProperty("creation_filetime").GetString() ||
                    !String.Equals(path.ToString(), expected.GetProperty("path").GetString(), StringComparison.OrdinalIgnoreCase))
                    throw new InvalidDataException("Process path/creation identity mismatch");
                Check();
            }
            catch { CloseHandle(handle); throw; }
        }
        internal void Check()
        {
            if (WaitForSingleObject(handle, 0) != 258) throw new InvalidOperationException("Bound process exited or wait failed");
        }
        public void Dispose() { CloseHandle(handle); }
    }

    public static class Capture
    {
        const uint LoopbackEventAutoConvert = 0x80060000;
        const int SampleRate = 44100, BlockAlign = 8, ActivationTimeoutMs = 10000;
        [DllImport("ole32.dll")] static extern int CoInitializeEx(IntPtr reserved, uint concurrency);
        [DllImport("ole32.dll")] static extern void CoUninitialize();
        [DllImport("Mmdevapi.dll", ExactSpelling = true, CharSet = CharSet.Unicode)]
        static extern int ActivateAudioInterfaceAsync(string device, ref Guid iid, ref PropVariant parameters,
            [MarshalAs(UnmanagedType.Interface)] ICompletion completion, out IActivationOperation operation);
        [DllImport("kernel32.dll")] static extern bool QueryPerformanceCounter(out long value);
        [DllImport("kernel32.dll")] static extern bool QueryPerformanceFrequency(out long value);
        [DllImport("kernel32.dll")] static extern void GetSystemTimePreciseAsFileTime(out long value);

        static void Check(int hr) { Marshal.ThrowExceptionForHR(hr); }
        static string Number(long value) { return value.ToString(CultureInfo.InvariantCulture); }
        static void Write(StreamWriter journal, object row) { journal.WriteLine(JsonSerializer.Serialize(row)); }
        static void Anchor(StreamWriter journal)
        {
            long before, after, utc, frequency;
            if (!QueryPerformanceFrequency(out frequency) || !QueryPerformanceCounter(out before))
                throw new InvalidOperationException("Native QPC unavailable");
            GetSystemTimePreciseAsFileTime(out utc);
            if (!QueryPerformanceCounter(out after)) throw new InvalidOperationException("Native QPC unavailable");
            Write(journal, new { kind = "anchor", qpc_before = Number(before), qpc_after = Number(after),
                utc_filetime = Number(utc), frequency = Number(frequency) });
        }

        static IAudioClient Activate(uint pid, ProcessLease target, ProcessLease parent)
        {
            if (IntPtr.Size != 8 || Marshal.SizeOf<ActivationParams>() != 12 ||
                Marshal.SizeOf<PropVariant>() != 24 || Marshal.SizeOf<WaveFormat>() != 18)
                throw new PlatformNotSupportedException("x64 SDK ABI mismatch");
            IntPtr memory = Marshal.AllocHGlobal(12);
            var completion = new Completion();
            IActivationOperation operation = null;
            try
            {
                Marshal.StructureToPtr(new ActivationParams { Type = 1, TargetPid = pid, Mode = 0 }, memory, false);
                var variant = new PropVariant { Type = 65, Blob = new Blob { Bytes = 12, Data = memory } };
                Guid iid = typeof(IAudioClient).GUID;
                Check(ActivateAudioInterfaceAsync("VAD\\Process_Loopback", ref iid, ref variant, completion, out operation));
                var timer = Stopwatch.StartNew();
                while (!completion.Done.Wait(50))
                {
                    parent.Check(); target.Check();
                    if (timer.ElapsedMilliseconds >= ActivationTimeoutMs) throw new TimeoutException("Process audio activation timeout");
                }
                Check(completion.Result);
                target.Check(); parent.Check();
                return (IAudioClient)completion.Activated;
            }
            finally
            {
                // Pending native activation owns the parameter memory until process exit.
                if (completion.Done.IsSet) Marshal.FreeHGlobal(memory);
                GC.KeepAlive(operation); GC.KeepAlive(completion);
            }
        }

        static void Drain(IAudioCaptureClient capture, FileStream pcm, StreamWriter journal,
                          ref long framesWritten, ref int packetsWritten)
        {
            uint available;
            Check(capture.GetNextPacketSize(out available));
            while (available > 0)
            {
                IntPtr pointer; uint frames, flags; ulong position, qpc;
                Check(capture.GetBuffer(out pointer, out frames, out flags, out position, out qpc));
                try
                {
                    if (frames == 0 || frames > SampleRate || qpc == 0 || (flags & ~3u) != 0 ||
                        (packetsWritten > 0 && (flags & 1) != 0))
                        throw new InvalidDataException("Invalid native packet geometry/timestamp/flags");
                    var bytes = new byte[checked((int)frames * BlockAlign)];
                    // WASAPI SILENT authorizes these exact frames, not absent packets.
                    if ((flags & 2) == 0)
                    {
                        if (pointer == IntPtr.Zero) throw new InvalidDataException("Null nonsilent packet");
                        Marshal.Copy(pointer, bytes, 0, bytes.Length);
                    }
                    pcm.Write(bytes, 0, bytes.Length);
                    Write(journal, new { kind = "packet", seq = packetsWritten, offset_bytes = framesWritten * BlockAlign,
                        frames, flags, qpc_100ns = qpc.ToString(CultureInfo.InvariantCulture),
                        device_position = position.ToString(CultureInfo.InvariantCulture) });
                    framesWritten += frames; packetsWritten++;
                }
                finally { Check(capture.ReleaseBuffer(frames)); }
                Check(capture.GetNextPacketSize(out available));
            }
        }

        public static int Run(string requestPath)
        {
            using var document = JsonDocument.Parse(File.ReadAllText(requestPath));
            JsonElement request = document.RootElement, identity = request.GetProperty("identity");
            string token = request.GetProperty("token").GetString();
            double seconds = request.GetProperty("max_seconds").GetDouble();
            if (String.IsNullOrEmpty(token) || !Double.IsFinite(seconds) || seconds <= 0 || seconds > 3600)
                throw new InvalidDataException("Invalid session token/duration");
            using var target = new ProcessLease(identity);
            using var parent = new ProcessLease(request.GetProperty("parent"));
            string directory = Path.GetDirectoryName(Path.GetFullPath(requestPath));
            using var pcm = new FileStream(Path.Combine(directory, "process_audio.f32"), FileMode.CreateNew, FileAccess.ReadWrite, FileShare.Read);
            using var journal = new StreamWriter(new FileStream(Path.Combine(directory, "process_audio.jsonl"), FileMode.CreateNew, FileAccess.Write, FileShare.Read), new UTF8Encoding(false));
            long framesWritten = 0;
            int packetsWritten = 0;
            object service = null;
            IAudioClient client = null;
            bool started = false, clean = false;
            string failure = null;
            Check(CoInitializeEx(IntPtr.Zero, 0)); // MTA; callback is explicitly agile.
            try
            {
                client = Activate(identity.GetProperty("pid").GetUInt32(), target, parent);
                var format = new WaveFormat { Tag = 3, Channels = 2, Rate = SampleRate,
                    BytesPerSecond = SampleRate * BlockAlign, Align = BlockAlign, Bits = 32 };
                Check(client.Initialize(0, LoopbackEventAutoConvert, 0, 0, ref format, IntPtr.Zero));
                Guid iid = typeof(IAudioCaptureClient).GUID;
                Check(client.GetService(ref iid, out service));
                var capture = (IAudioCaptureClient)service;
                using var available = new AutoResetEvent(false);
                Check(client.SetEventHandle(available.SafeWaitHandle.DangerousGetHandle()));
                Write(journal, new { kind = "ready", schema = 1, identity, token, mode = "include_target_tree",
                    format = new { rate_hz = SampleRate, channels = 2, sample_format = "f32le" } });
                Anchor(journal);
                target.Check(); parent.Check();
                Check(client.Start()); started = true;
                // Console's synchronized TextReader may block synchronously even
                // in ReadLineAsync; it must not stall the WASAPI packet thread.
                Task<string> command = Task.Run(() => Console.In.ReadLine());
                var timer = Stopwatch.StartNew();
                double nextAnchor = 0.5;
                bool announced = false;
                while (true)
                {
                    target.Check(); parent.Check();
                    if (timer.Elapsed.TotalSeconds > seconds) throw new TimeoutException("Audio capture duration exceeded");
                    if (command.IsCompleted)
                    {
                        if (command.GetAwaiter().GetResult() != "STOP " + token)
                            throw new InvalidOperationException("Parent EOF or invalid STOP token");
                        Check(client.Stop()); started = false;
                        Drain(capture, pcm, journal, ref framesWritten, ref packetsWritten);
                        target.Check(); parent.Check();
                        clean = true;
                        break;
                    }
                    available.WaitOne(50);
                    Drain(capture, pcm, journal, ref framesWritten, ref packetsWritten);
                    if (!announced && packetsWritten > 0)
                    {
                        journal.Flush(); pcm.Flush();
                        Console.WriteLine("READY " + token); Console.Out.Flush(); announced = true;
                    }
                    if (timer.Elapsed.TotalSeconds >= nextAnchor)
                    {
                        Anchor(journal); journal.Flush();
                        nextAnchor = timer.Elapsed.TotalSeconds + 0.5;
                    }
                }
            }
            catch (Exception error) { failure = error.GetType().Name + ": " + error.Message; }
            finally
            {
                try { if (started) Check(client.Stop()); }
                catch (Exception error) { clean = false; failure = "Stop failed: " + error.Message; }
                if (service != null) Marshal.ReleaseComObject(service);
                if (client != null) Marshal.ReleaseComObject(client);
                CoUninitialize();
            }
            Anchor(journal);
            pcm.Flush(); pcm.Position = 0;
            string hash = Convert.ToHexString(SHA256.HashData(pcm)).ToLowerInvariant();
            Write(journal, new { kind = "terminal", clean, reason = clean ? "STOP" : "ERROR", token,
                target_alive = clean, frames = framesWritten, packets = packetsWritten, bytes = pcm.Length,
                pcm_sha256 = hash, error = failure });
            journal.Flush();
            Console.WriteLine((clean ? "CLOSED " : "FAILED ") + token); Console.Out.Flush();
            return clean ? 0 : 1;
        }
    }
}
