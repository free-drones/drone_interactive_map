/**
 * AttentionBorder component. Screen wide border for especially attention-needing tasks, like defining area of interest.
 */

import React from "react";
import { Typography, Popover } from "@mui/material/";
import { Box } from "@mui/system";
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
    color: "#000000",
    boxShadow: (theme) => theme.shadows[5],
    borderRadius: (theme) => theme.spacing(1),
    backgroundColor: "rgba(255,255,255,0.75)",

    zIndex: (theme) => theme.zIndex.appBar - 1,

    cursor: "pointer",
    userSelect: "none",

    ...(theme) => theme.typography.button,
  },
  infoButton: {
    zIndex: "appBar",
    position: "relative",
    left: "3%",
    top: "3px",
    color: "#0075B7",
  },
};

/**
 * AttentionBorder component function.
 */
export function AttentionBorder(props) {
  const [showInformation, setShowInformation] = React.useState(false);
  const helpButton = React.useRef(null);
  return (
    <div>
      <Box
        sx={styles.borderHead}
        onClick={() => setShowInformation(!showInformation)}
        ref={helpButton}
      >
        <Typography variant="h6" component="h2" elevation={10}>
          {props.children}
          <HelpIcon sx={styles.infoButton} />
        </Typography>
        <Popover
          open={showInformation}
          anchorEl={helpButton.current}
          onClose={() => setShowInformation(false)}
          anchorOrigin={{
            vertical: "bottom",
            horizontal: "center",
          }}
          transformOrigin={{
            horizontal: "center",
            vertical: "top",
          }}
        >
          <Typography sx={{ p: 2 }}>
            Click/tap the map to place nodes in the shape of a polygon with at
            least 3 nodes.
            <br />
            <br />
            Confirm the area by pressing the the green check mark button in the
            bottom right corner.
            <br />
            <br />
            The button will turn green when 3 or more nodes are placed with no
            crossing (red) lines in the polygon.
          </Typography>
        </Popover>
      </Box>
      <Box sx={styles.borderBox} />
    </div>
  );
}
