import { Box, Typography } from "@mui/material";
import { userPriority, connect } from "../Storage.js";

const styles = {
  priorityIndicator: {
    position: "absolute",
    width: "100%",
    height: "100%",
    left: 0,
    top: 0,
    zIndex: "appBar",
    display: "flex",
    justifyContent: "center",
    pointerEvents: "none",
  },
  shadowedText: {
    color: "#333",
    textShadow: "2px 2px white",
  },
};

function UserPriorityIndicator(props) {
  if (props.store.userPriority === 1) {
    return "";
  }
  return (
    <Box sx={styles.priorityIndicator}>
      <Typography sx={styles.shadowedText} variant="h3">
        Low priority
      </Typography>
    </Box>
  );
}

export default connect({ userPriority })(UserPriorityIndicator);
