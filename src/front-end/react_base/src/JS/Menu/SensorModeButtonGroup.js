/**
 * Class file for radiobuttons regarding picture mode.
 */
import React, { Component } from 'react';
import RadioGroup from '@mui/material/RadioGroup';
import { connect, sensor, sensorActions } from '../Storage.js';
import Typography from '@mui/material/Typography';
import FormControlLabel from '@mui/material/FormControlLabel';
import Radio from '@mui/material/Radio';

class SensorModeButtonGroup extends Component {

    constructor() {
        super();
        this.onRadioChange = this.onRadioChange.bind(this);
    }

    onRadioChange = (e) => {
        this.props.store.setSensor(e.target.value);
    }

    render() {
        return (
            <div >
                <RadioGroup value={this.props.store.sensor} onChange={this.onRadioChange}>
                    <Typography variant="h5">
                        Sensor:
                    </Typography>
                    <FormControlLabel value="RGB" control={<Radio />} label="RGB" />
                    <FormControlLabel value="IR" control={<Radio />} label="IR" />
                    <FormControlLabel value="Map" control={<Radio />} label="Map" />
                </RadioGroup>
            </div>
        );
    }
}


export default connect({ sensor }, { ...sensorActions })(SensorModeButtonGroup);


