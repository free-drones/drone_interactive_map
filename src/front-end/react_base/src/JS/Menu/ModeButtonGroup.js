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
    }
}

export default connect({ mapPosition, mode }, { ...mapPositionActions, ...modeActions })(ModeButtonGroup);


