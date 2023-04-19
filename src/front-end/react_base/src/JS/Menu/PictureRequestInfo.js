/**
 * Component containing information about a picture request.
 */

import React from "react";

import Typography from "@mui/material/Typography";
import { Box } from "@mui/system";

/**
 * Get a formatted time string form at date object.
 * @param {Date} date Date to be formatted.
 */
function getFormattedTime(date) {
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  const seconds = String(date.getSeconds()).padStart(2, "0");

  return hours + ":" + minutes + ":" + seconds;
}

function getTimeSince(currentTime, date) {
  const seconds = Math.floor((currentTime - date) / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(seconds / (60 * 60));

  return `${hours}h ${minutes % (60 * 60)}m ${seconds % 60}s ago`;
}

export default function PictureRequestInfo({ data }) {
  const [time, setTime] = React.useState(Date.now());
  setTimeout(() => {
    setTime(Date.now()); // Used to make the component rerender every second to show the actual time since
  }, 1000);
  return (
    <div>
      <Box>
        <Typography variant="subtitle1" display="block">
          {data.isUrgent ? "Urgent " : "Normal "} Picture Request
        </Typography>
        <Typography variant="subtitle2" display="block">
          {"Request time: " + getFormattedTime(new Date(data.requestTime))}
        </Typography>
        <Typography variant="subtitle2" display="block">
          {getTimeSince(time, data.requestTime)}
        </Typography>
        {data.received ? (
          <Typography variant="subtitle2" display="block">
            {"Receive time: " + getFormattedTime(new Date(data.receiveTime))}
          </Typography>
        ) : (
          ""
        )}
      </Box>
    </div>
  );
}
