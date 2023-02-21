/**
 * Class file for camera queue indicator.
 */
import React, { Component } from 'react';
import Badge from '@mui/material/Badge';
import CameraAltIcon from '@mui/icons-material/CameraAlt';
import { connect, requestQueue } from "../Storage.js";


class CameraQueueIcon extends Component {
    render() {
        return (
            <Badge
                badgeContent={this.props.store.requestQueue.size}
                color="primary"
                anchorOrigin={{ vertical: 'top', horizontal: 'left' }}
                showZero
            >
                <CameraAltIcon />
            </Badge>
        );
    }
}

export default connect({ requestQueue }, {})(CameraQueueIcon);
