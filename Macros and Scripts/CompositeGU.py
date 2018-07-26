import os
from ij import IJ
from array import array
from fiji.util.gui import GenericDialogPlus
from java.awt import Dimension
from ij.plugin.frame import RoiManager
from ij.io import DirectoryChooser
from java.awt.event import MouseAdapter, KeyEvent, KeyAdapter
from ij.gui import GenericDialog, WaitForUserDialog, GenericDialog, Roi, PointRoi, Toolbar, Overlay
from javax.swing import (BoxLayout, ImageIcon, JButton, JFrame, JPanel,
        JPasswordField, JLabel, JTextArea, JTextField, JScrollPane,
        SwingConstants, WindowConstants, Box)

# create variables
iROI = 0
xlist = ylist = zlist = []

def getImage():
	gdp = GenericDialogPlus("Choose Input Movie")
	gdp.addFileField("Myosin Movie", "")
	gdp.showDialog()
	inputImage = gdp.getNextString()
	print("Selected File:"+ inputImage)
	return inputImage


def reset(manager):
    global iROI, xlist, ylist, zlist
    xlist = []
    ylist = []
    zlist = []
    manager.runCommand('Reset')
    manager.runCommand('Show All with labels')
    iROI = 0
def updateROIs(manager):
	
    global iROI, xlist, ylist, zlist
    iROI += 1
    canv = imp.getCanvas()
    p = canv.getCursorLoc()
    z = imp.getCurrentSlice()
    roi = PointRoi(p.x , p.y )
    xlist.append(p.x)
    ylist.append(p.y)
    zlist.append(z)
    imp.setRoi(roi)
    manager.addRoi(roi)
    manager.runCommand('Add')
    manager.runCommand('Draw')
    manager.runCommand('Show All with labels')
 

def drawCircle(event):
	defaultRadius = 0
	radiusText.setText(str(defaultRadius))

def moveSlice(event):
	moveTo = int(moveText.getText())
	imp.setSlice(moveTo)

def startChoose(event):
	manager = RoiManager.getInstance()
	if manager is None:
	    manager = RoiManager()

	##user defines parameter values:
	reset(manager)

	class ML(MouseAdapter):
		def mousePressed(self, keyEvent):
			updateROIs(manager)
	#Listeners:
	listener = ML()
	win = imp.getWindow()
	win.getCanvas().addMouseListener(listener)
	manager.runCommand('Measure')

def saveChoices(event):
	dc = DirectoryChooser("Pick folder for saving ROI set")
	folder = dc.getDirectory()
	manager = RoiManager.getInstance()
	manager.runCommand('Measure') 
	IJ.saveAs("Results",  folder + "Choices.csv");

	for index in range(0,iROI,1):
		print("Here!")
		previousSlice = zlist[index]
		newSlice = previousSlice + 1
		imp.setSlice(newSlice)
		imp.setRoi(PointRoi(xlist[index],ylist[index]));
		newRoi = imp.getRoi();
		manager.addRoi(newRoi);
	
	
#	manager.reset();
#	manager.close()

inputImage = getImage()
imp = IJ.openImage(inputImage)
IJ.setTool(Toolbar.POINT)
imp.show()
numberOfSlices = imp.getNSlices()

frame = JFrame(inputImage,size = (500, 200))
frame.setTitle(str(inputImage))

panel = JPanel()
panel.setLayout(BoxLayout(panel, BoxLayout.Y_AXIS))
frame.add(panel)
###textField 

numberOfSlicesLabel = JLabel("Total Time Points:"+str(numberOfSlices))
panel.add(numberOfSlicesLabel)

###Point picking panel
choosePanel = JPanel()
choosePanel.setLayout(BoxLayout(choosePanel, BoxLayout.X_AXIS))
moveLabel = JLabel("Move to time")
moveLabel.setBounds(60,20,40,20)
moveText = JTextField(10)
moveText.setBounds(120,20,60,20)
moveButton = JButton("Move", actionPerformed = moveSlice)
startChoosingButton = JButton("Start Choosing", actionPerformed = startChoose)
endChoosingButton = JButton("Save And Overlay", actionPerformed = saveChoices)
choosePanel.add(Box.createVerticalGlue())
choosePanel.add(moveLabel)
choosePanel.add(moveText)
choosePanel.add(Box.createRigidArea(Dimension(10,0)))
choosePanel.add(moveButton)
choosePanel.add(Box.createRigidArea(Dimension(10,0)))
choosePanel.add(startChoosingButton)
choosePanel.add(Box.createRigidArea(Dimension(10,0)))
choosePanel.add(endChoosingButton)
###Radius panel
radiusPanel = JPanel()
radiusPanel.setLayout(BoxLayout(radiusPanel, BoxLayout.X_AXIS))
radiusLabel = JLabel("Radius (in pixels)")
radiusLabel.setBounds(60,20,40,20)
radiusText = JTextField(10)
radiusText.setBounds(120,20,60,20)
radiusUpdateButton = JButton("Draw Circle", actionPerformed = drawCircle)
radiusPanel.add(Box.createVerticalGlue())
radiusPanel.add(radiusLabel)
radiusPanel.add(radiusText)
radiusPanel.add(Box.createRigidArea(Dimension(25,0)))
radiusPanel.add(radiusUpdateButton)
###Point panel
pointPanel = JPanel()
pointPanel.setLayout(BoxLayout(pointPanel, BoxLayout.X_AXIS))
previousPointButton = JButton("<- Point")
nextPointButton = JButton("Point ->")
pointPanel.add(Box.createVerticalGlue())
pointPanel.add(previousPointButton)
pointPanel.add(Box.createRigidArea(Dimension(25,0)))
pointPanel.add(nextPointButton)
###Slice panel
slicePanel = JPanel()
slicePanel.setLayout(BoxLayout(slicePanel, BoxLayout.X_AXIS))
previousSliceButton = JButton("<- Time")
nextSliceButton = JButton("Time -> ")
slicePanel.add(Box.createVerticalGlue())
slicePanel.add(previousSliceButton)
slicePanel.add(Box.createRigidArea(Dimension(25,0)))
slicePanel.add(nextSliceButton)
###Save & Quit panel
saveAndQuitPanel = JPanel()
saveAndQuitPanel.setLayout(BoxLayout(saveAndQuitPanel, BoxLayout.X_AXIS))
saveButton = JButton("Save")
quitButton = JButton("Quit ")
saveAndQuitPanel.add(Box.createVerticalGlue())
saveAndQuitPanel.add(saveButton)
saveAndQuitPanel.add(Box.createRigidArea(Dimension(25,0)))
saveAndQuitPanel.add(quitButton)

panel.add(choosePanel)
panel.add(radiusPanel)
panel.add(pointPanel)
panel.add(slicePanel)
panel.add(saveAndQuitPanel)

frame.visible = True;
