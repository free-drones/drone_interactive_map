import React, { Component } from "react";
import {
  Slider,
  FormGroup,
  FormControlLabel,
  Switch,
  Typography,
} from "@mui/material";
import { connect, config, configActions } from "../Storage.js";

class DroneIconConfigGroup extends Component {
  render() {
    return (
      <FormGroup>
        <Typography variant="h5">Drone Icons:</Typography>
        <FormControlLabel
          label="Size"
          labelPlacement="top"
          control={
            <Slider
              sx={{ padding: "10px !important" }}
              value={this.props.store.config.droneIconPixelSize}
              valueLabelDisplay="auto"
              step={1}
              min={10}
              max={30}
              onChange={(e, val) =>
                this.props.store.setConfigValue("droneIconPixelSize", val)
              }
            />
          }
        />
        <FormControlLabel
          control={
            <Switch
              checked={this.props.store.config.showDroneIcons}
              onChange={(e, val) =>
                this.props.store.setConfigValue("showDroneIcons", val)
              }
            />
          }
          label="Visibility"
        />
      </FormGroup>
    );
  }
}

export default connect({ config }, { ...configActions })(DroneIconConfigGroup);
