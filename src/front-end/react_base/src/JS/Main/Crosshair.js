/**
 * Crosshair component shows a crosshair in the middle of the screen.
 */

import React from "react";

import Typography from "@mui/material/Typography";
import { Box } from "@mui/system";

const styles = {
  centeredChildren: {
    position: "absolute",
    top: 0,
    left: 0,
    width: "100%",
    height: "100%",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",

    zIndex: (theme) => theme.zIndex.appBar,
    pointerEvents: "none",
  },
};

/**
 * AttentionBorder component function.
 */
export default function Crosshair() {
  return (
    <div>
      <Box sx={styles.centeredChildren}>
        <Typography variant="h6" component="h2">
          &#x271B;
        </Typography>
      </Box>
    </div>
  );
}
