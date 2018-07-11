from ij import IJ
from ij.plugin.frame import RoiManager
from ij.gui import WaitForUserDialog


imp = IJ.openImage("/Users/prakash/Desktop/BobSegDataAndResults/GoodData/2018-06-05_fromMark/20180604_LP823_Control-03_Coupled/MyosinStack.tif");

imp.show()

IJ.run("Set Scale...", "distance=0 known=0 pixel=1 unit=pixel");

WaitForUserDialog("","Move to slice where myosins are to be selected").show() 


IJ.run("ROI Manager...");
WaitForUserDialog("Select ROIs","Add myosins to ROI Manager").show() 
	
	
roi = RoiManager.getRoiManager()
roi_points = roi.getRoisAsArray()
a= imp.getCurrentSlice();
	
dir = IJ.getDirectory("/Users/prakash/Desktop/BobSegDataAndResults/GoodData/2018-06-05_fromMark/20180604_LP823_Control-03_Coupled/FlowQunatification/"); 
IJ.run("Measure"); 
IJ.saveAs("Results",  dir + "time_00"+ str(a) +".csv");
start_frame = a;
end_frame = a+1;
	 
for repeat in range(start_frame,end_frame,1):
	
	
	imp.setSlice(a+1)
	
	roi.runCommand(imp,"Show All");
	WaitForUserDialog("","Select last ROI and hit B").show()
	imp.setSlice(a+1)
	WaitForUserDialog("","Select last ROI").show() 
	imp.setSlice(a+1)
	#roi.select(2);
	IJ.run(imp, "Add Selection...", "");
	
	roi.reset();
	
	WaitForUserDialog("Myosin Movement","Select new ROIs").show()
	
	combi_roi = RoiManager.getRoiManager()
	combi_roi_points = roi.getRoisAsArray()
	print(combi_roi_points)
	print(len(combi_roi_points))
	
	dir = IJ.getDirectory("/Users/prakash/Desktop/BobSegDataAndResults/FlowQuantification/"); 
	IJ.run("Measure"); 
	IJ.saveAs("Results",  dir +  "time_00"+ str(a+1) +".csv"); 
	
	#roi.close();
	
	a= a+1;
	imp.setSlice(a)


