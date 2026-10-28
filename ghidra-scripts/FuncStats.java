import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
public class FuncStats extends GhidraScript {
  public void run() throws Exception {
    int total=0, named=0; StringBuilder sb=new StringBuilder();
    for (Function f : currentProgram.getFunctionManager().getFunctions(true)) {
      if(f.getEntryPoint().getOffset()<0x80000000L) continue; total++; String n=f.getName();
      if(!n.startsWith("FUN_")){named++; if(named<=40) sb.append(n).append(" @ ").append(f.getEntryPoint()).append("\n");}
    }
    println("TOTAL="+total+" NAMED="+named+" UNNAMED="+(total-named));
    println(sb.toString());
  }
}
