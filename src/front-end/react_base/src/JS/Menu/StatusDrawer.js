/**
 * Tab styled drawer for status information.
 */

import React from "react";
import TabDrawer from "./TabDrawer";
import TabDrawerTab from "./TabDrawerTab";
import CameraQueueIcon from "./CameraQueueIcon.js";
import SmsFailedIcon from "@mui/icons-material/SmsFailed";
import MessagesTab from "./MessagesTab";
import { connect, pictureRequestQueue, pictureRequestQueueActions } from "../Storage.js";
import PriorityImagesTab from "./PriorityImagesTab";

function StatusDrawer() {
  return (
    <div>
      <TabDrawer anchor="right">
        <TabDrawerTab icon={<CameraQueueIcon />}>
          <PriorityImagesTab />
        </TabDrawerTab>
        <TabDrawerTab icon={<SmsFailedIcon />}>
          <MessagesTab />
        </TabDrawerTab>
      </TabDrawer>
    </div>
  );
}

export default connect(
  { pictureRequestQueue },
  { ...pictureRequestQueueActions }
)(StatusDrawer);
