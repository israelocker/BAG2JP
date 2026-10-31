"""Drive real keyboard inputs near the native beat and retain observed combat outcomes."""
import argparse,ctypes,json,re,time,os
from pathlib import Path
from ctypes import wintypes

def read_watch(path):
    with Path(path).open('rb') as stream:
        stream.seek(max(0,stream.seek(0,2)-16384));raw=stream.read();lines=raw.split(b'\n')[:-1]
    for line in reversed(lines):
        if len(re.findall(rb'[0-9A-F]{8}=',line))==16:
            return {key.decode():int(value,16) for key,value in re.findall(rb'([0-9A-F]{8})=([0-9A-F]+)',line)}
    return {}

def is_combat(state):
    return state.get('8005D2C4')==2 and state.get('8005D3D4')==0x13 and state.get('8005E65A')==3

def trace_rows(path):
    with Path(path).open('rb') as stream:
        stream.seek(max(0,stream.seek(0,2)-16384));data=stream.read()
    return [tuple(map(int,match.groups())) for match in re.finditer(rb'f(\d+)[^\n]*P1 ch\d+ anim(\d+) req(\d+) \| P2 ch\d+ anim(\d+) req(\d+)\r?\n',data)]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid',type=int,required=True);parser.add_argument('--exe',type=Path,required=True)
    parser.add_argument('--watch',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--seconds',type=float,default=170)
    parser.add_argument('--stop-on-proof',action='store_true')
    parser.add_argument('--observe-only',action='store_true');args=parser.parse_args()
    if not 0<args.seconds<=600:raise ValueError('Test duration must be within 1..600 seconds')
    user=ctypes.WinDLL('user32',use_last_error=True);kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.restype=wintypes.HANDLE;handle=kernel.OpenProcess(0x1000,False,args.pid)
    if not handle:raise OSError('Cannot inspect target process')
    kernel.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)]
    name=ctypes.create_unicode_buffer(32768);length=wintypes.DWORD(len(name))
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    try:
        if not kernel.QueryFullProcessImageNameW(handle,0,name,ctypes.byref(length)):raise OSError('Cannot verify executable')
    finally:kernel.CloseHandle(handle)
    if os.path.normcase(name.value)!=os.path.normcase(str(args.exe.resolve())):raise ValueError('Unexpected target executable')
    user.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
    user.IsWindowVisible.argtypes=[wintypes.HWND];user.IsWindow.argtypes=[wintypes.HWND]
    user.GetWindowRect.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.RECT)]
    windows=[];callback_type=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
    @callback_type
    def collect(hwnd,unused):
        pid=wintypes.DWORD();user.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
        if pid.value==args.pid and user.IsWindowVisible(hwnd):windows.append(hwnd)
        return True
    user.EnumWindows.argtypes=[callback_type,wintypes.LPARAM]
    user.EnumWindows(collect,0)
    if not windows:raise ValueError('No target game window')
    hwnd=windows[0];user.PostMessageW.argtypes=[wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM]
    def key(code,down):
        scan=user.MapVirtualKeyW(code,0);bits=1|(scan<<16)
        if not down:bits|=0xC0000000
        if not user.PostMessageW(hwnd,0x100 if down else 0x101,code,bits):raise OSError('Key post failed')
    args.output.mkdir(parents=True,exist_ok=False)
    from PIL import ImageGrab
    def shot(name):
        rect=wintypes.RECT();user.GetWindowRect(hwnd,ctypes.byref(rect))
        ImageGrab.grab((rect.left,rect.top,rect.right,rect.bottom)).save(args.output/name)
    trace=args.watch.with_name('bag2jp_anim_trace.log');initial=trace_rows(trace);last_trace=initial[-1][0] if initial else -1
    started=time.monotonic();scheduled=set();events=[];outcomes=[];release=None;pending_shots=[];seen=set();trial=0
    try:
        while time.monotonic()-started<args.seconds and user.IsWindow(hwnd):
            now=time.monotonic()
            if release and now>=release[1]:key(release[0],False);release=None
            state=read_watch(args.watch)
            if not state:time.sleep(.005);continue
            clock=state['800892EC'];start=state['8005E71E'];goal=start+state['8005E2DA']
            for frame,anim1,req1,anim2,req2 in trace_rows(trace):
                if frame<=last_trace:continue
                last_trace=frame
                for side,(animation,request) in enumerate(((anim1,req1),(anim2,req2))):
                    if request in (101,102,110,170,171,172,123,124,125,126,127,128,129,140,141,142,150,151,152,*range(200,211)):
                        row={'clock':clock,'frame':frame,'side':side,'animation':animation,'request':request};outcomes.append(row)
                        if (side,request) not in seen:
                            seen.add((side,request));pending_shots.append((clock+12,f'p{side+1}-request{request}-{frame}.png'))
                            print('Observed',json.dumps(row),flush=True)
            for due,name in pending_shots[:]:
                if clock>=due:shot(name);pending_shots.remove((due,name))
            valid=not args.observe_only and is_combat(state)
            if valid and start not in scheduled and goal-10<=clock<=goal+1:
                incoming1=state['8005E786']!=0;incoming2=state['8005E754']!=0
                diff=state['8005E6CC'];d1=diff&255;d2=diff>>8
                if incoming1:
                    reflect=trial%2==1;side=0;kind='reflect' if reflect else 'guard';offset=-1 if reflect else -4
                    code=ord(('S' if d1>1 else 'W') if reflect else ('X' if d1>1 else 'R'))
                elif incoming2:
                    side=1;kind='stock_dodge';offset=-3;code=ord('F' if d2>1 else 'N')
                else:
                    side=0 if {(0,171),(0,172)}<=seen else 1
                    kind='attack';offset=-1;code=ord(('S' if d1>1 else 'W') if side==0 else ('G' if d2>1 else 'B'))
                if clock>=goal+offset:
                    key(code,True);release=(code,now+.04);scheduled.add(start)
                    events.append({'clock':clock,'goal':goal,'side':side,'action':kind,'key':chr(code),'incoming1':incoming1,'incoming2':incoming2})
                    if incoming1:trial+=1
                    print('Input',json.dumps(events[-1]),flush=True)
            if args.stop_on_proof and {(0,171),(0,172),(0,123)}<=seen and not pending_shots:break
            time.sleep(.003)
    finally:
        if release:
            try:
                if user.IsWindow(hwnd):key(release[0],False)
            except OSError:pass
        (args.output/'combat.json').write_text(json.dumps({'inputs':events,'outcomes':outcomes,'seconds':time.monotonic()-started},indent=2))
    proof_met={(0,171),(0,172),(0,123)}<=seen
    print(json.dumps({'inputs':len(events),'outcomes':len(outcomes),'observed_requests':sorted(seen),'proof_met':proof_met}))
    return 2 if args.stop_on_proof and not proof_met else 0
if __name__=='__main__':raise SystemExit(main())
