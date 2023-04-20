/**
 * List item to store information about the pictures requested to be taken. 
 * They are stored in the PriorityPicturesTab.
 */

import {
  ListItem,
  ListItemText,
  ListItemIcon,
  Typography,
  Collapse,
} from "@mui/material";

import React from "react";

import { ExpandMore, ChevronRight } from "@mui/icons-material/";

import PriorityPictureRequestInfo from "./PriorityPictureRequestInfo.js";

const styles = {
  thinIcon: {
    alignSelf: "flex-start",
    cursor: "pointer",
  },
  wrappingText: {
    whiteSpace: "normal",
    marginLeft: 3,
},
  listItem: {
    display: "flex",
    flexDirection: "column",
    alignItems: "flex-end",
  },
};

/**
 * React component used to show information about a priority picture request in a list item
 * @param {Object} item priority picture request data
 * @param {Number} listID 
 * @returns React component
 */
export default function PriorityPictureListItem({ item, listID }) {
  const [shouldShowInfo, setShouldShowInfo] = React.useState(false);
  return (
    <ListItem sx={styles.listItem} key={item.requestTime}>
      <ListItemIcon
        sx={styles.thinIcon}
        onClick={() => setShouldShowInfo(!shouldShowInfo)}
      >
        {shouldShowInfo ? <ExpandMore /> : <ChevronRight />}
        <Typography variant="body1">Picture Request {listID}</Typography>
      </ListItemIcon>
      <Collapse in={shouldShowInfo}>
        <ListItemText
          disableTypography
          sx={styles.wrappingText}
          //   primary={<Typography variant="body1">{item.id}</Typography>}
          secondary={<PriorityPictureRequestInfo data={item} />}
        />
      </Collapse>
    </ListItem>
  );
}
