/**
 * Tab drawer tab for priority image requests.
 */

import React from "react";
import { useState } from "react";

import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import ListItemIcon from "@mui/material/ListItemIcon";

import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import {
  Dialog,
  DialogActions,
  DialogTitle,
  DialogContent,
} from "@mui/material";

import Divider from "@mui/material/Divider";

import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import Redo from "@mui/icons-material/Redo";
import Check from "@mui/icons-material/Check";

import {
  connect,
  pictureRequestQueue,
  pictureRequestQueueActions,
} from "../Storage.js";

import { clearImageQueue, callbackWrapper } from "../Connection/Downstream";
import ColorWrapper from "../ColorWrapper.js";
import PictureRequestInfo from "./PictureRequestInfo.js";

const styles = {
  fullWidthButton: {
    flexGrow: 1,
    justifyContent: "center",
  },
  thinIcon: {
    minWidth: (theme) => theme.spacing(2),
    alignSelf: "flex-start",
  },
  wrappingText: {
    whiteSpace: "normal",
    margin: 0,
  },
};

function PriorityImagesTab(props) {
  var [dialogOpen, setDialogState] = useState(false);

  return (
    <div>
      {/* Clear priority queue button */}
      <ListItem>
        <ColorWrapper color="decline">
          <Button
            variant="contained"
            onClick={() => setDialogState(true)}
            startIcon={<Redo />}
          >
            Clear queue
          </Button>
        </ColorWrapper>
      </ListItem>

      <Divider />

      <List>
        {/* Sort requests on request time, then add all to list */}
        {[...props.store.pictureRequestQueue]
          .sort((i1, i2) => i2.requestTime - i1.requestTime)
          .map((item) => (
            <ListItem key={item.requestTime}>
              <ListItemIcon sx={styles.thinIcon}>
                {item.received ? <Check /> : <ChevronRightIcon />}
              </ListItemIcon>
              <ListItemText
                disableTypography
                sx={styles.wrappingText}
                primary={<Typography variant="body1">{item.id}</Typography>}
                secondary={<PictureRequestInfo data={item} />}
              />
            </ListItem>
          ))}
      </List>

      <Dialog
        open={dialogOpen}
        onClose={() => {
          setDialogState(false);
        }}
      >
        <DialogTitle>Confirm clearing of request queue.</DialogTitle>
        <DialogContent>
          Are you sure you want to clear the queue of image requests?
        </DialogContent>
        <DialogActions>
          <ColorWrapper color="decline">
            <Button
              onClick={() => {
                setDialogState(false);
              }}
            >
              Cancel
            </Button>
          </ColorWrapper>
          <ColorWrapper color="accept">
            <Button
              onClick={() =>
                clearImageQueue(
                  callbackWrapper(() => {
                    props.store.clearPictureRequestQueue();
                    setDialogState(false);
                  })
                )
              }
            >
              Confirm
            </Button>
          </ColorWrapper>
        </DialogActions>
      </Dialog>
    </div>
  );
}

export default connect(
  { pictureRequestQueue },
  { ...pictureRequestQueueActions }
)(PriorityImagesTab);
