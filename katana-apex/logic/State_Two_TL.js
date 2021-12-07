var logger = executor.logger;
var time = new Date();

logger.info("##START## State_Two_TL");

var report = executor.inFields.get("report");
logger.info("~~report: " + report);

var alertAlbumSize = executor.getContextAlbum("Alerts_Album").size();
logger.info("~~Alert Album has: " + alertAlbumSize + " elements");

var alertAlbumData = executor.getContextAlbum("Alerts_Album").get(String(alertAlbumSize-1));
logger.info("~~Got alert message from context with this timestamp: " + alertAlbumData.timestamp);

// Do something for State
executor.getExecutionProperties().setProperty("sliceId", alertAlbumData.sliceId);

executor.outFields.put("report", "Completed State Two");

logger.info("##END## State_Two_TL");

var returnValue = true;
returnValue;
