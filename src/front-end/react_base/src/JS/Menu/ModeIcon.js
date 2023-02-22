/**
 * Class file for Mode indicator.
 */
import React, { Component } from 'react';
import Badge from '@mui/material/Badge';
import SettingsIcon from '@mui/icons-material/Settings';
import { connect, mode, modeActions } from "../Storage.js";


class ModeIcon extends Component {
    render() {
        return (
            <Badge
                badgeContent={this.props.store.mode[0]}
                color="primary"
                anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
                showZero
            >
                <SettingsIcon />
            </Badge>
        );
    }
}

export default connect({ mode }, { ...modeActions })(ModeIcon);
