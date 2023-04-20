/**
 * Tab drawer tab for priority image requests.
 */

import React from "react";
import { useState } from "react";

import {
  List,
  ListItem,
  Button,
  Divider,
  Dialog,
  DialogActions,
  DialogTitle,
  DialogContent,
} from "@mui/material";

import { Redo } from "@mui/icons-material/";

import {
  connect,
  pictureRequestQueue,
  pictureRequestQueueActions,
} from "../Storage.js";

import PriorityPictureListItem from "./PriorityPictureListItem.js";

import { clearImageQueue, callbackWrapper } from "../Connection/Downstream.js";
import ColorWrapper from "../ColorWrapper.js";

function PriorityPicturesTab(props) {
  const [dialogOpen, setDialogState] = useState(false);
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
          .map((item, index) => (
            <PriorityPictureListItem
              item={item}
              listID={props.store.pictureRequestQueue.length - index}
            />
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
)(PriorityPicturesTab);
