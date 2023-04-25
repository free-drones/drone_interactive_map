/**
 * Tab styled drawer for settings.
 */

import React, { useState } from "react";
import TabDrawer from "./TabDrawer.js";
import TabDrawerTab from "./TabDrawerTab.js";
import {
  Button,
  Dialog,
  DialogActions,
  DialogTitle,
  DialogContent,
  ListItem,
} from "@mui/material";
import { Navigate } from "react-router-dom";
import ModeButtonGroup from "./ModeButtonGroup.js";
import LayerTypeModeButtonGroup from "./LayerTypeModeButtonGroup.js";
import UndoIcon from "@mui/icons-material/Undo";
import {
  connect,
  areaWaypoints,
  areaWaypointActions,
  requestQueueActions,
  mapState,
  mapStateActions,
  activePicturesActions,
  userPriority,
  showWarning,
  showWarningActions,
} from "../Storage.js";
import ModeIcon from "./ModeIcon.js";
import ColorWrapper from "../ColorWrapper.js";
import DroneIconConfigGroup from "./DroneIconConfigGroup.js";

const styles = {
  fullWidthButton: {
    flexGrow: 1,
    justifyContent: "center",
  },
};

function SettingsDrawer(props) {
  var [dialogOpen, setDialogState] = useState(false);
  var [redirected, redirect] = useState(false);
  redirect = redirect.bind(true);

  /**
   * ClickHandler for redefine button pressed. Opens dialog window.
   */
  function redefineClickHandler() {
    setDialogState(true);
    props.store.setShowWarning(false);
  }

  /**
   * ClickHandler for confirmed dialog window. Reroutes to StartUp.
   */
  function reroute() {
    setDialogState(false);

    props.store.clearActivePictures();
    props.store.setMapState("StartUp");
    redirect(true);
  }

  return (
    <div>
      {redirected ? <Navigate to="/StartUp" /> : <div />}

      <TabDrawer anchor="left">
        <TabDrawerTab icon={<ModeIcon />}>
          <ListItem>
            <ModeButtonGroup />
          </ListItem>
          <ListItem>
            <LayerTypeModeButtonGroup />
          </ListItem>
          <ListItem>
            <DroneIconConfigGroup />
          </ListItem>
          <div style={{ flexGrow: 1 }} />
          <ListItem>
            <ColorWrapper color="decline">
              <Button
                sx={styles.fullWidthButton}
                variant="contained"
                onClick={redefineClickHandler}
                startIcon={<UndoIcon />}
                disabled={props.store.userPriority !== 1}
              >
                Redefine area
              </Button>
            </ColorWrapper>
          </ListItem>
        </TabDrawerTab>
      </TabDrawer>

      <Dialog
        open={dialogOpen}
        onClose={() => {
          setDialogState(false);
        }}
      >
        <DialogTitle>Confirm redefining area of interest.</DialogTitle>
        <DialogContent>
          Are you sure you want to redefine the area of interest?
        </DialogContent>
        <DialogActions>
          <ColorWrapper color="decline">
            <Button
              onClick={() => {
                setDialogState(false);
              }}
              color="secondary"
            >
              Cancel
            </Button>
          </ColorWrapper>
          <ColorWrapper color="accept">
            <Button onClick={reroute}>Confirm</Button>
          </ColorWrapper>
        </DialogActions>
      </Dialog>
    </div>
  );
}

export default connect(
  { userPriority, areaWaypoints, mapState, showWarning },
  {
    ...areaWaypointActions,
    ...mapStateActions,
    ...requestQueueActions,
    ...activePicturesActions,
    ...showWarningActions,
  }
)(SettingsDrawer);
