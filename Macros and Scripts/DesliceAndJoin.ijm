function deSlice(input, filename){
	open(input + filename);
	run("Make Substack...", "  slices=6-6"); //Change slices= as needed. This line makes substack of 1 frame for picking out a mysoin frame at a particular focal plane
	saveAs("Tiff", output+filename);
}



input = "/Users/prakash/Desktop/BobSegDataAndResults/GoodData/2018-06-05_fromMark/20180604_LP823_Control-07_Uncoupled/myosin/"; //Change as needed. This is the input directory where all images are stored
output = "/Users/prakash/Desktop/BobSegDataAndResults/GoodData/2018-06-05_fromMark/20180604_LP823_Control-07_Uncoupled/deSlice/06/"; //Change as needed. This is the output directory where per frame substacks need to be stored



setBatchMode(true); 
list = getFileList(input);
for (i = 0; i < list.length; i++)
	deSlice(input, list[i]);
setBatchMode(false);

setBatchMode(true); 
list2 = getFileList(output);

for (j = 0; j < list2.length; j++){
	open(output + list2[j]);
}

run("Images to Stack", "name=Stack title=[] use"); 
saveAs("Tiff", output+"Stack"+"06.tif"); //Change as needed. This is where the desliced focal planes for each time frames are joined together to make a time-lapse movie of differnt focal planes
close();
setBatchMode(false);
