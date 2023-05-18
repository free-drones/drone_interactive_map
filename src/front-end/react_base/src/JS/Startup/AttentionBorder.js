/**
 * AttentionBorder component. Screen wide border for especially attention-needing tasks, like defining area of interest.
 */

import React from "react";
import Typography from "@mui/material/Typography";
import { Box } from "@mui/system";
import { Opacity } from "@mui/icons-material";
import HelpIcon from "@mui/icons-material/Help";

const styles = {
  borderBox: {
    position: "absolute",

    overflow: "hidden",

    height: (theme) => `calc(100% - ${theme.spacing(4)})`,
    width: (theme) => `calc(100% - ${theme.spacing(4)})`,

    top: "50%",
    left: "50%",
    transform: "translate(-50%, -50%)",

    borderColor: "error.main",
    borderStyle: "dashed",
    borderWidth: (theme) => theme.spacing(1),
    borderRadius: (theme) => theme.spacing(1),

    pointerEvents: "none",

    zIndex: "appBar",
  },
  borderHead: {
    position: "absolute",

    top: (theme) => theme.spacing(3),
    left: "50%",
    transform: "translate(-50%, 0)",

    padding: (theme) => theme.spacing(1),
    //color: "error.main",
    color: "#000000",
    boxShadow: (theme) => theme.shadows[5],
    borderRadius: (theme) => theme.spacing(1),
    backgroundColor: "rgba(255,255,255,0.75)",

    zIndex: (theme) => theme.zIndex.appBar - 1,

    pointerEvents: "auto",

    ...(theme) => theme.typography.button,
  },
  infoButton: {
    zIndex: "appBar",
    position: "relative",
    left: "3%",
    top: "3px",
    color: "#0075B7",
    userSelect:"none",
  },
  
};


/**
 * AttentionBorder component function.
 */
export function AttentionBorder(props) {
  return (
    <div>
      <Box sx={styles.borderHead} onClick={() => alert("Click/ tapp the map to place nodes that will create a polygon after 3 nodes.\n\nConfirm the area by pressing the the green check mark button in the bottom right corner.\n\nThe button will turn green when 3 or more nodes are placed with no crossing (red) lines in the polygon.")}>
        <Typography variant="h6" component="h2" elevation={10}>
          {props.children}
          <HelpIcon sx={styles.infoButton}  />
        </Typography>
      </Box>
      <Box sx={styles.borderBox} />
    </div>
  );
}
