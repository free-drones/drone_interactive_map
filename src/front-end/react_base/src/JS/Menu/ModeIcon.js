/**
 * Class file for Mode indicator.
 */
import React, { Component } from "react";
import { Badge, Box } from "@mui/material";
import SettingsIcon from "@mui/icons-material/Settings";
import { connect, mode, modeActions } from "../Storage.js";

class ModeIcon extends Component {
  render() {
    return (
      <Box sx={{ display: "flex" }}>
        <SettingsIcon />
        <Badge
          badgeContent={this.props.store.mode}
          color="primary"
          showZero
          sx={{ left: 16 }}
        ></Badge>
      </Box>
    );
  }
}

export default connect({ mode }, { ...modeActions })(ModeIcon);
