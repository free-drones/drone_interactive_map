/**
 * Class file for radiobuttons regarding run mode.
 */

import React, { Component } from 'react';
import RadioGroup from '@mui/material/RadioGroup';
import { setMode, callbackWrapper } from "../Connection/Downstream.js";
import { connect, mapPosition, mapPositionActions, modeActions, mode } from "../Storage.js"
import Typography from '@mui/material/Typography';
import FormControlLabel from '@mui/material/FormControlLabel';
import Radio from '@mui/material/Radio';
import { userPrio } from '../Storage.js';

class ModeButtonGroup extends Component {

    constructor() {
        super();
        this.onRadioChange = this.onRadioChange.bind(this);
    }

    /**
     * On change event for radio button.
     * Changes active button and sends mode to back-end.
     */
    onRadioChange = (e) => {
        //Send to backend
        var newMode = e.target.value;

        setMode(newMode, this.props.store.mapPosition, callbackWrapper((response) => {
            // Update stored state
            this.props.store.setMode(newMode);
        }));

    }

    render() {
        console.log(this.props.store.userPrio)
        switch(this.props.store.userPrio) {
            case 1:
                return (
                    <div >
                    <RadioGroup value={this.props.store.mode} onChange={this.onRadioChange}>
                        <Typography variant="h5">
                            Mode:
                        </Typography>
                        <FormControlLabel value="MAN" control={<Radio />} label="Manual" />
                        <FormControlLabel value="AUTO" control={<Radio />} label="Auto" />
                    </RadioGroup>
                </div>    
                );
            default:
                return (
                    <div >
                    <RadioGroup value={this.props.store.mode} onChange={this.onRadioChange}>
                        <Typography variant="h5">
                            Mode:
                        </Typography>
                        <FormControlLabel control={<Radio />} label="Manual" disabled />
                        <FormControlLabel control={<Radio />} label="Auto" disabled />
                    </RadioGroup>
                </div>    
                );
        }
    }
}

export default connect({ userPrio, mapPosition, mode }, { ...mapPositionActions, ...modeActions })(ModeButtonGroup);


