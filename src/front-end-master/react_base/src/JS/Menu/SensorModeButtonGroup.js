/**
 * Class file for radiobuttons regarding picture mode.
 */
import React, { Component } from 'react';
import RadioGroup from '@material-ui/core/RadioGroup';
import { connect, sensor, sensorActions } from '../Storage.js';
import Typography from '@material-ui/core/Typography';
import FormControlLabel from '@material-ui/core/FormControlLabel';
import Radio from '@material-ui/core/Radio';

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


