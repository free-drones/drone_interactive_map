/**
 * Class file for radio buttons regarding picture mode.
 */
import React, { Component } from "react";
import RadioGroup from "@mui/material/RadioGroup";
import { connect, layerType, layerTypeActions } from "../Storage.js";
import Typography from "@mui/material/Typography";
import FormControlLabel from "@mui/material/FormControlLabel";
import Radio from "@mui/material/Radio";

class LayerTypeModeButtonGroup extends Component {
  constructor() {
    super();
    this.onRadioChange = this.onRadioChange.bind(this);
  }

  onRadioChange = (e) => {
    this.props.store.setLayerType(e.target.value);
  };

  render() {
    return (
      <div>
        <RadioGroup
          value={this.props.store.layerType}
          onChange={this.onRadioChange}
        >
          <Typography variant="h5">Layer Type:</Typography>
          <FormControlLabel value="RGB" control={<Radio />} label="RGB" />
          <FormControlLabel value="IR" control={<Radio />} label="IR" />
          <FormControlLabel value="Map" control={<Radio />} label="Map" />
        </RadioGroup>
      </div>
    );
  }
}

export default connect(
  { layerType },
  { ...layerTypeActions }
)(LayerTypeModeButtonGroup);
