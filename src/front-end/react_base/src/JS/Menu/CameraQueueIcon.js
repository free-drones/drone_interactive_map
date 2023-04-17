/**
 * Class file for camera queue indicator.
 */
import React, { Component } from "react";
import Badge from "@mui/material/Badge";
import CameraAltIcon from "@mui/icons-material/CameraAlt";
import { connect, pictureRequestQueue } from "../Storage.js";

class CameraQueueIcon extends Component {
  render() {
    return (
      <Badge
        badgeContent={this.props.store.pictureRequestQueue.length}
        color="primary"
        anchorOrigin={{ vertical: "top", horizontal: "left" }}
        showZero
      >
        <CameraAltIcon />
      </Badge>
    );
  }
}

export default connect({ pictureRequestQueue }, {})(CameraQueueIcon);
