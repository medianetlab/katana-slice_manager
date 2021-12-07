var logger = executor.logger;
var time = new Date();

logger.info("##START## Example_TL");

var input = executor.inFields.get("input");
logger.info("~~input: " + input);

executor.getContextAlbum("Context_Album").put(input, time.toString());
logger.info("~~Time of input stored: " + time + " in Context_Album");

var contextAlbumData = executor.getContextAlbum("Context_Album").get(input);
logger.info("~~Grab time from Context Album");

executor.outFields.put("output", contextAlbumData);

logger.info("##END## Example_TL");

var returnValue = true;
returnValue;
