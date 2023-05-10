/**
 * Class file for camera button component.
 */

import {
  Fab,
  Box,
  Button,
  ButtonGroup,
  Collapse,
  ButtonBase,
} from "@mui/material";
import { AddAPhoto, NoPhotography } from "@mui/icons-material/";
import React from "react";
import { userPriority, isInsideArea, connect } from "../Storage.js";
import Crosshair from "./Crosshair.js";

const styles = {
  cameraButton: {
    position: "absolute",
    zIndex: "appBar",

    bottom: (theme) => theme.spacing(2),
    left: "50%",
    transform: "translate(-50%, 0)", //transform ensures position is in the middle
  },
  pictureDarkenOverlay: {
    position: "fixed",
    top: 0,
    left: 0,
    width: "100%",
    height: "100%",
    // backgroundColor: "#50505066",
    pointerEvents: "none",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
  },
  extendedFabLike: {
    backgroundColor: "white",
    display: "flex",
    borderRadius: "4px",
  },
  extendedButton: {
    padding: 2,
  },
};

function getPictureFocusStyle(isInsideArea) {
  return {
    boxShadow: `0 0 0 9999px ${isInsideArea ? "#50505066" : "#99000066"}`,
    height: "20vh", // Matches the size of the requested image
    width: `${20 * (4 / 3)}vh`, // Matches the size of the requested image
  };
}

/**
 * A floating camera button component which extends into selecting urgency and also has an overlay.
 */
function CameraButton(props) {
  const [shouldChooseUrgency, setShouldChooseUrgency] = React.useState(false);
  return (
    <Box>
      {shouldChooseUrgency ? (
        <Box sx={styles.pictureDarkenOverlay}>
          <Box sx={getPictureFocusStyle(props.store.isInsideArea)}>
            <Crosshair />
          </Box>
        </Box>
      ) : (
        ""
      )}
      {/* Creates the extended urgency selection button */}
      <Collapse
        sx={styles.cameraButton}
        in={shouldChooseUrgency}
        timeout="auto"
        orientation="horizontal"
      >
        <Box sx={styles.extendedFabLike}>
          <ButtonGroup variant="outlined" disabled={!props.store.isInsideArea}>
            <ButtonBase
              sx={styles.extendedButton}
              onClick={() => setShouldChooseUrgency(false)}
            >
              <NoPhotography />
            </ButtonBase>
            <Button
              sx={styles.extendedButton}
              color="info"
              onClick={() => {
                props.clickHandler(false);
                setShouldChooseUrgency(false);
              }}
            >
              Normal
            </Button>
            <Button
              sx={styles.extendedButton}
              color="error"
              onClick={() => {
                props.clickHandler(true);
                setShouldChooseUrgency(false);
              }}
            >
              Urgent
            </Button>
          </ButtonGroup>
        </Box>
      </Collapse>
      {/* Creates a floating object, Fab */}
      {!shouldChooseUrgency ? (
        <Fab
          sx={[styles.cameraButton, { backgroundColor: "white" }]}
          onClick={() => {
            setShouldChooseUrgency(true);
          }}
          disabled={props.store.userPriority !== 1}
        >
          <AddAPhoto />
        </Fab>
      ) : (
        ""
      )}
    </Box>
  );
}
export default connect({ userPriority, isInsideArea })(CameraButton);
