/**
 * Tab styled drawer for status information.
 */

import React from "react";
import TabDrawer from "./TabDrawer";
import TabDrawerTab from "./TabDrawerTab";
import CameraQueueIcon from "./CameraQueueIcon.js";
import SmsFailedIcon from "@mui/icons-material/SmsFailed";
import MessagesTab from "./MessagesTab";
import { connect, requestQueue, requestQueueActions } from "../Storage.js";
import PrioImagesTab from "./PrioImagesTab";

function StatusDrawer() {
  return (
    <div>
      <TabDrawer anchor="right">
        <TabDrawerTab icon={<CameraQueueIcon />}>
          <PrioImagesTab />
        </TabDrawerTab>
        <TabDrawerTab icon={<SmsFailedIcon />}>
          <MessagesTab />
        </TabDrawerTab>
      </TabDrawer>
    </div>
  );
}

export default connect(
  { requestQueue },
  { ...requestQueueActions }
)(StatusDrawer);
