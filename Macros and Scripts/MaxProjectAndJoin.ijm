function action(input, output, filename) {
        open(input + filename);
        run("Z Project...", "projection=[Max Intensity]");
        saveAs("Tiff", output+filename);
        close();
}

input = "/Users/prakash/Desktop/BobSegDataAndResults/GoodData/2018-06-05_fromMark/20180604_LP823_Control-07_Uncoupled/membrane/"; //Change as needed. This is the input directory where all images are stored
output = "/Users/prakash/Desktop/BobSegDataAndResults/GoodData/2018-06-05_fromMark/20180604_LP823_Control-07_Uncoupled/MaxProjectedMembrane/"; //Change as needed. This is the output directory where per frame max pfrojections need to be stored


setBatchMode(true); 
list = getFileList(input);
for (i = 0; i < list.length; i++)
	action(input, output, list[i]);
setBatchMode(false);

setBatchMode(true); 
list2 = getFileList(output);

for (j = 0; j < list2.length; j++){
	open(output + list2[j]);
}

run("Images to Stack", "name=Stack title=[] use");
saveAs("Tiff", "/Users/prakash/Desktop/BobSegDataAndResults/GoodData/2018-06-05_fromMark/20180604_LP823_Control-07_Uncoupled/MembraneStack.tif"); //Change as needed. This is where the different max projected frames are merged together to make a time-lapse movie.
close();
close();
setBatchMode(false);