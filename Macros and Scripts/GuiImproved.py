import os
from ij import IJ, WindowManager
from array import array
from fiji.util.gui import GenericDialogPlus
from java.awt import Dimension, Color
from ij.plugin.frame import RoiManager
from ij.measure import ResultsTable
from ij.io import DirectoryChooser
from java.awt.event import MouseAdapter, KeyEvent, KeyAdapter
from ij.gui import GenericDialog, WaitForUserDialog, GenericDialog, Roi, PointRoi, Toolbar, Overlay, OvalRoi, Line
from javax.swing import (BoxLayout, ImageIcon, JButton, JFrame, JPanel,
        JPasswordField, JLabel, JTextArea, JTextField, JScrollPane,
        SwingConstants, WindowConstants, Box, KeyStroke)
 
# create variables
iROI = 0
iTrackROI =0
xlist = ylist = zlist = []
trackEvent = 0

def getImage():
	gdp = GenericDialogPlus("Choose Input Movie")
	gdp.addFileField("Myosin Movie", "")
	gdp.showDialog()
	inputImage = gdp.getNextString()
	print("Selected File:"+ inputImage)
	return inputImage


def reset():
    global iROI, xlist, ylist, zlist, radiiList, iTrackROI
    xlist = []
    ylist = []
    zlist = []
    radiiList = []
    manager = RoiManager.getInstance()
    manager.runCommand('Reset')
    manager.runCommand('Show All')
    iROI = 0
    iTrackROI = 0
   
    
def updateROIs():
	
    global iROI, xlist, ylist, zlist, xTracklist, yTracklist, zTracklist
    iROI += 1
    canv = imp.getCanvas()
    p = canv.getCursorLoc()
    z = imp.getCurrentSlice()
    print(z)
    roi = PointRoi(p.x , p.y )
    xTracklist = []
    yTracklist = []
    zTracklist = []
    if(trackEvent ==0):
    	xlist.append(p.x)
    	ylist.append(p.y)
    	zlist.append(z)
    elif (trackEvent == 1):
    	xTracklist.append(p.x)
    	yTracklist.append(p.y)
    	zTracklist.append(z)
    imp.setRoi(roi)
    manager = RoiManager.getInstance()
    manager.addRoi(roi)
#    manager.runCommand('Add')
#    manager.runCommand('Draw')
    manager.runCommand('Show All')

def drawCircle(event):
	radius = int(radiusText.getText())
	print(xTracklist[0])
	roi = OvalRoi(xTracklist[0]-radius, yTracklist[0]-radius, radius*2, radius*2);
	imp.setRoi(roi)

def confirmCircle(event):
	radiiList.append(int(radiusText.getText()))
	table = ResultsTable.getResultsTable();
	table.incrementCounter();
	table.addValue("center_x", xTracklist[0]);
	table.addValue("center_y", yTracklist[0]);
	table.addValue("radius",int(radiusText.getText()));
	table.addValue("slice", zTracklist[0]);
	table.show("Results");
	
def moveSlice(event):
	moveTo = int(moveText.getText())
	imp.setSlice(moveTo)

def moveToPreviousPoint(event):
	table = ResultsTable.getResultsTable();
	tableCounter = table.getCounter();
	previousROI = array('i',[tableCounter-1])
	manager = RoiManager.getInstance()
	manager.setSelectedIndexes(previousROI)

def moveToNextPoint(event):
	table = ResultsTable.getResultsTable();
	tableCounter = table.getCounter();
	nextROI = array('i',[tableCounter])
	print(nextROI)
	manager = RoiManager.getInstance()
	imp.setSlice(imp.getCurrentSlice()-1)
	manager.selectAndMakeVisible(imp, tableCounter) 
	
def startChoose(event):
	manager = RoiManager.getInstance()
	if manager is None:
	    manager = RoiManager()

	##user defines parameter values:
	reset()

	class ML(MouseAdapter):
		def mousePressed(self, keyEvent):
			updateROIs()
	#Listeners:
	listener = ML()
	win = imp.getWindow()
	win.getCanvas().addMouseListener(listener)
	manager.runCommand('Measure')

def overlayChoices(event):
	startChoosingButton.enabled = 0
	dc = DirectoryChooser("Pick folder for saving ROI set")
	folder = dc.getDirectory()
	manager = RoiManager.getInstance()
	manager.runCommand('Measure') 
	IJ.saveAs("Results",  folder + "Choices.csv");
	table = ResultsTable.getResultsTable();
	table.reset()

	

	for index in range(0,iROI,1):
		previousSlice = zlist[index]
		newSlice = previousSlice + 1
		imp.setSlice(newSlice)
		roi1 = PointRoi(xlist[index],ylist[index])
		roi1.setPosition(newSlice)
		roi1.setStrokeColor(Color.red)
		roi2 = PointRoi(xlist[index],ylist[index])
		roi2.setPosition(newSlice-1)
		roi2.setStrokeColor(Color.yellow)
		overlay.add(roi1)
		overlay.add(roi2)
		imp.setOverlay(overlay)
		
	#roi.setStrokeWidth(1)

def chooseTracked(event):
	global trackEvent 
	trackEvent = 1
	endChoosingButton.enabled = 0
	manager = RoiManager.getInstance()
	selection = manager.getSelectedIndex()
	if(selection == -1):
		selectROI = array('i',[0])
		manager.setSelectedIndexes(selectROI)
	else:
		selection = manager.getSelectedIndexes()
		setSelectionIndex = selection[0]+1
		selectROI = array('i',[setSelectionIndex])
		manager.setSelectedIndexes(selectROI)

def movePreviousTime(event):
		imp.setSlice(imp.getCurrentSlice()-1)

def moveNextTime(event):
		imp.setSlice(imp.getCurrentSlice()+1)

def saveTracks(event):
	dc = DirectoryChooser("Pick folder for saving tracks with radii")
	folder = dc.getDirectory()
	table = ResultsTable.getResultsTable();
	table.save(folder+ "savedtracks.csv");
	table.reset()

def quit(event):
	imp.close();
	JFrame.dispose(frame);

def doSomething(imp, keyEvent):
  """ A function to react to key being pressed on an image canvas. """
  if(keyEvent.getKeyCode() ==77): # Move shortcut-> M
  	moveSlice(keyEvent)
  if(keyEvent.getKeyCode() ==10): # Start choosing myosins to track shortcut ->Enter
  	startChoose(keyEvent)
  if(keyEvent.getKeyCode() ==79): # Overlay selected myosins and save shortcut -> O
  	overlayChoices(keyEvent)
  if(keyEvent.getKeyCode() ==16): # Choose tracked myosins shortcut -> Shift
  	chooseTracked(keyEvent)
  if(keyEvent.getKeyCode() ==68): # Draw circle shortcut -> D
  	drawCircle(keyEvent)
  if(keyEvent.getKeyCode() ==67): # Confirm circle shortcut -> C
  	confirmCircle(keyEvent)
  if(keyEvent.getKeyCode() ==76): # Next myosin shortcut -> L
  	moveToNextPoint(keyEvent)
  if(keyEvent.getKeyCode() ==75): # Previous myosin shortcut -> K
  	moveToPreviousPoint(keyEvent)
  if(keyEvent.getKeyCode() ==44): # Next time -> >
  	movePreviousTime(keyEvent)
  if(keyEvent.getKeyCode() ==46): # Previous time -> <
  	moveNextTime(keyEvent)
  if(keyEvent.getKeyCode() ==83): # Save -> S
  	saveTracks(keyEvent)
  if(keyEvent.getKeyCode() ==81): # Quit shortcut ->Q
  	quit(keyEvent)
  # Prevent further propagation of the key event:
  keyEvent.consume()
 

	
### Main code starts here

inputImage = getImage()
imp = IJ.openImage(inputImage)
IJ.setTool(Toolbar.POINT)
imp.show()
numberOfSlices = imp.getNSlices()
overlay = Overlay()

#roi = Line(30,70,230,230)
#roi.setStrokeColor(Color.red)
#roi.setStrokeWidth(1)
#overlay.add(roi)

frame = JFrame(inputImage,size = (800, 200))
frame.setTitle(str(inputImage))
#frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE)


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
moveText = JTextField("1",10)
moveText.setBounds(120,20,60,20)
moveButton = JButton("Move", actionPerformed = moveSlice)
startChoosingButton = JButton("Start Choosing Mysoins to Track", actionPerformed = startChoose)
endChoosingButton = JButton("Overlay Selected And Save", actionPerformed = overlayChoices)
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
chooseSecondButton = JButton("Choose tracked myosins", actionPerformed = chooseTracked)
radiusLabel = JLabel("Radius (in pixels)")
radiusLabel.setBounds(60,20,40,20)
radiusText = JTextField("0",10)
radiusText.setBounds(120,20,60,20)
radiusUpdateButton = JButton("Draw Circle/ Update Circle", actionPerformed = drawCircle)
radiusConfirmButton = JButton("Confirm Circle", actionPerformed = confirmCircle)
radiusPanel.add(Box.createVerticalGlue())
radiusPanel.add(chooseSecondButton)
radiusPanel.add(Box.createRigidArea(Dimension(25,0)))
radiusPanel.add(radiusLabel)
radiusPanel.add(radiusText)
radiusPanel.add(Box.createRigidArea(Dimension(25,0)))
radiusPanel.add(radiusUpdateButton)
radiusPanel.add(Box.createRigidArea(Dimension(25,0)))
radiusPanel.add(radiusConfirmButton)
###Point panel
pointPanel = JPanel()
pointPanel.setLayout(BoxLayout(pointPanel, BoxLayout.X_AXIS))
previousPointButton = JButton("<- Previous Selected Myosin", actionPerformed = moveToPreviousPoint)
nextPointButton = JButton("Next Selected Myosin ->", actionPerformed = moveToNextPoint)
pointPanel.add(Box.createVerticalGlue())
pointPanel.add(previousPointButton)
pointPanel.add(Box.createRigidArea(Dimension(25,0)))
pointPanel.add(nextPointButton)
###Slice panel
slicePanel = JPanel()
slicePanel.setLayout(BoxLayout(slicePanel, BoxLayout.X_AXIS))
previousSliceButton = JButton("<- Time", actionPerformed = movePreviousTime)
nextSliceButton = JButton("Time -> ", actionPerformed = moveNextTime)
slicePanel.add(Box.createVerticalGlue())
slicePanel.add(previousSliceButton)
slicePanel.add(Box.createRigidArea(Dimension(25,0)))
slicePanel.add(nextSliceButton)
###Save & Quit panel
saveAndQuitPanel = JPanel()
saveAndQuitPanel.setLayout(BoxLayout(saveAndQuitPanel, BoxLayout.X_AXIS))
saveButton = JButton("Save", actionPerformed = saveTracks)
quitButton = JButton("Quit ", actionPerformed = quit)
#quitButton = JButton("Quit ")
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

class ListenToKey(KeyAdapter):
  def keyPressed(this, event):
    imp = event.getSource().getImage()
    doSomething(imp, event)
  
listener = ListenToKey()
 
for imp in map(WindowManager.getImage, WindowManager.getIDList()):
  win = imp.getWindow()
  if win is None:
    continue
  canvas = win.getCanvas()
  # Remove existing key listeners
  kls = canvas.getKeyListeners()
  map(canvas.removeKeyListener, kls)
  # Add our key listener
  canvas.addKeyListener(listener)

