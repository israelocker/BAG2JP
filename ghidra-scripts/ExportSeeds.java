import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import java.io.*; import java.util.*;
public class ExportSeeds extends GhidraScript {
  public void run() throws Exception {
    String[] a=getScriptArgs(); long lo=Long.decode(a[0]), hi=Long.decode(a[1]);
    PrintWriter seeds=new PrintWriter(new FileWriter(a[2])); PrintWriter syms=new PrintWriter(new FileWriter(a[3]));
    Set<String> seen=new HashSet<>(); int n=0,s=0;
    for (Function f: currentProgram.getFunctionManager().getFunctions(true)) {
      long pc=f.getEntryPoint().getOffset(); if(pc<lo||pc>=hi) continue;
      seeds.printf("0x%08X%n",pc); n++;
      String nm=f.getName();
      if(nm.startsWith("FUN_")||!nm.matches("[A-Za-z_][A-Za-z0-9_]*")||!seen.add(nm)) continue;
      syms.printf("%n[[func]]%npc = 0x%08X%nname = \"%s\"%nemit = false%nstatus = \"guessed\"%nnote = \"Ghidra psx_ldr PsyQ signature\"%n",pc,nm); s++;
    }
    seeds.close(); syms.close(); println("SEEDS="+n+" SYMS="+s);
  }
}
