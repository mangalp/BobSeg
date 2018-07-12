from ij import IJ
from ij.plugin.frame import RoiManager
from ij.gui import WaitForUserDialog, OvalRoi, GenericDialog
from ij.measure import ResultsTable

def getOptions():
    global listener, xlist, ylist, zlist, manager
    gd = GenericDialog("radius Selection")
    gd.addNumericField("radius (pixel)", 3, 0)
    gd.showDialog()
    radius = gd.getNextNumber()
    return radius

def getConfirmation():
	gd1 = GenericDialog("radius confirmation")
	gd1.addMessage('Press 1 if circle is good, else select 0. Selecting 0 asks for new radius \n')
	gd1.addChoice('type', ['1', '0'], '1')
	gd1.showDialog()
	profileType = gd1.getNextChoice()
	return profileType


# configuration
folder = "/Users/prakash/Desktop/";
radiiList = []

# reset the table at the beginning
table = ResultsTable.getResultsTable();
table.reset()

imp = IJ.openImage("/Users/prakash/Desktop/BobSegDataAndResults/GoodData/2018-06-05_fromMark/20180604_LP823_Control-03_Coupled/MyosinStack.tif");

imp.show()

IJ.run("Set Scale...", "distance=0 known=0 pixel=1 unit=pixel");

WaitForUserDialog("","Move to slice where myosins are to be selected").show() 


IJ.run("ROI Manager...");
WaitForUserDialog("Select ROIs","Add myosins to ROI Manager").show() 
	
	
roi = RoiManager.getRoiManager()
roi_points = roi.getRoisAsArray()
print(roi_points)
print("Coordinates:")
for i in range (0, len(roi_points)):
		p = roi_points[i].getPolygon()
		x = p.xpoints
		y = p.ypoints

		#for u in range (0,len(x)):
			
			#print(x[u])
			#print(y[u])
a= imp.getCurrentSlice();
i = 0
j =0

while (i< len(x)):
	
	radius = getOptions()
	roi = OvalRoi(x[i]-radius, y[i]-radius, radius*2, radius*2);
	imp.setRoi(roi)
	profileType = getConfirmation()
	print(profileType)
	
	if (int(profileType) is 0):
		print("i:", i)
	else:
		j = j+1
		radiiList.append(radius)
		# write the analysed values in a table
		table = ResultsTable.getResultsTable();
		table.incrementCounter();
		table.addValue("center_x", x[i]);
		table.addValue("center_y",y[i]);
		table.addValue("radius",radius);
		table.show("Results");
		
	i = j

# save the table
table = ResultsTable.getResultsTable();
table.show("Results");
table.save(folder + "sampleResults.csv");
table.reset()
		
print(radiiList)

IJ.run("Close All", "");
	

	
		

