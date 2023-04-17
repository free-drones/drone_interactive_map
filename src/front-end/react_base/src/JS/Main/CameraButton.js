/**
 * Class file for camera button component.
 */

import { Fab, Box, Button, ButtonGroup, Collapse } from "@mui/material";
import { AddAPhoto } from "@mui/icons-material/";
import React from "react";
import { userPriority, connect } from "../Storage.js";

const styles = {
  cameraButton: {
    position: "absolute",
    zIndex: "appBar",

    bottom: (theme) => theme.spacing(2),
    left: "50%",
    transform: "translate(-50%, 0)", //transform ensures position is in the middle
  },
};

function CameraButton(props) {
  const [shouldChooseUrgency, setShouldChooseUrgency] = React.useState(false);
  return (
    //Creates a floating object, Fab
    <Box sx={styles.cameraButton}>
      <Fab
        onClick={() => {
          setShouldChooseUrgency(!shouldChooseUrgency);
        }}
        disabled={props.store.userPriority !== 1}
        variant={shouldChooseUrgency ? "extended" : "round"}
        sx={
          shouldChooseUrgency
            ? { borderTopRightRadius: 3, borderBottomRightRadius: 3 } // Adjusts the radius to the button's radius during the urgency choice
            : {}
        }
      >
        <AddAPhoto sx={{ color: shouldChooseUrgency ? "gray" : "black" }} />
        <Collapse
          in={shouldChooseUrgency}
          timeout="auto"
          orientation="horizontal"
          sx={{
            height: "100% !important",
            width: shouldChooseUrgency ? "100% !important" : "",
          }} // Makes the buttons easier to click by covering the entire space
        >
          <ButtonGroup
            variant="outlined"
            sx={{ paddingLeft: 2, height: "100%", width: "100%" }}
          >
            <Button
              sx={{ width: "50%" }}
              color="info"
              onClick={() => props.clickHandler(false)}
            >
              Normal
            </Button>
            <Button
              sx={{ width: "51%" }} // The background goes out slightly longer, so 51% is needed
              color="error"
              onClick={() => props.clickHandler(true)}
            >
              Urgent
            </Button>
          </ButtonGroup>
        </Collapse>
      </Fab>
    </Box>
  );
}
export default connect({ userPriority })(CameraButton);
