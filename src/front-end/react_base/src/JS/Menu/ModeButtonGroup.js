/**
 * Class file for radiobuttons regarding run mode.
 */

import React, { Component } from 'react';
import RadioGroup from '@material-ui/core/RadioGroup';
import { setMode, callbackWrapper } from "../Connection/Downstream.js";
import { connect, mapPosition, mapPositionActions, modeActions, mode } from "../Storage.js"
import Typography from '@material-ui/core/Typography';
import FormControlLabel from '@material-ui/core/FormControlLabel';
import Radio from '@material-ui/core/Radio';

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


