open("/Users/prakash/Desktop/one.csv"); 
setTool("multipoint");
run("Point Tool...", "type=Crosshair color=Magenta size=Small label counter=0");
for (i=0; i<nResults; i++) { 
	slice = getResult("slice", i); 
    x = getResult("X", i); 
    y = getResult("Y", i); 
    
    run("Specify...", "width=1 height=1 x=&x y=&y slice=&slice oval");
    roiManager("Add"); 
    
	
 } 
roiManager("Associate", "true");
roiManager("Centered", "false");
roiManager("UseNames", "false");
roiManager("Show All"); 
