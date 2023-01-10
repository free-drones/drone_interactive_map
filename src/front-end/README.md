# Front end <!-- omit in toc -->
Here follows an overview and development guide of the Interactive Map Module (IMM) front-end.

- [File overview](#file-overview)
  - [Folders](#folders)
  - [Source](#source)
    - [CSS](#css)
    - [JS](#js)
    - [test](#test)
  - [Inclusion tree](#inclusion-tree)
- [Installing](#installing)
- [Running](#running)
- [Usage](#usage)
  - [Using Storage](#using-storage)
  - [Using connection](#using-connection)
  - [Using ColorWrapper](#using-colorwrapper)
  - [Using TabDrawers](#using-tabdrawers)
- [Extension](#extension)
  - [Extending components](#extending-components)
  - [Extending storage](#extending-storage)
      - [Action](#action)
      - [Reducer](#reducer)
      - [Mappings](#mappings)
      - [Final touches](#final-touches)
  - [Extending connection](#extending-connection)
- [Future development](#future-development)

## File overview

### Folders
The project is divided into static and dynamic parts - `public` and `src`. Images, the html index and the manifest are located in the `public` folder. These files should need to see minimal change. `src` contains all the working source code for the product and is further discussed below.

### Source
The source is divided into three subfolders - `CSS`, `JS` and `test`. 

#### CSS
`CSS` contains the static CSS styling sheets. Most components are styled dynamically with JSS, and the `CSS` folder therefore only contains one file. This style sheet is used by the Map component.

#### JS
`JS` contains most of the active code during runtime and is further subdivided into folders. A folder contains components that are usually seen together. 

#### test
`test` contains the test code for the project. Currently, only Storage and the code handling connection is tested. These tests are run with [jest](https://jestjs.io/). For running tests see [Running](#running).

### Inclusion tree
This is the inclusion tree for all React components in `src`. This is the order in which components get included in the product when served to the end user. **Note** that almost all files include parts of Storage and some communicate with the connection files, but these are not react components and have therefore been omitted. **Also note** that this is not always indicative of the React component hierarchy.

 - index.js
   - App.js
     - StartUp
       - AttentionBorder
       - IMMMap
       - ColorWrapper
     - Main
       - IMMMap
       - CameraButton
       - SettingsDrawer
         - TabDrawer
         - TabDrawerTab
         - ModeIcon
         - ColorWrapper
         - ModeButtonGroup
         - SensorModeButtonGroup
       - StatusDrawer
         - TabDrawer
         - TabDrawerTab
         - CameraQueueIcon
         - MessagesTab
           - ColorWrapper
         - PrioImageTab
           - ColorWrapper

## Installing
For developing [Node.js](https://nodejs.org/en/download/) is required. Once Node is installed Node Package Manager (NPM) can be used to automatically install all the dependencies of the project. This is done by running `npm install` in the `react_base` folder. This installs the packages listed in the `package.json` file.

For production any webserver can be used, but an easy alternative is to use Node with Serve. Server is installed globally by running `npm install -g serve`. For more information on building for production, see [react_base](react_base/README.md).

## Running
For info on running the app, both for production and development, see [react_base](react_base/README.md). There lies the default generated README file for Create React App projects.

To run a dummy server, for testing purposes, type `npm run mockup`. This starts a dumb mockup server to respond to the front end while developing. Front end will connect to this server if the `TESTING`-flag is set in `App.js`.

In production, the website can be hosted by running `serve -s your_build_folder`. 

## Usage

### Using Storage
To connect a React component to the Storage, the `connect` function of Storage is used. The connected storage states and actions are then accessible as props under `props.store`, for example `props.store.sensor` and `props.store.setSensor()`.

To access the store from non component environments the `dispatch` function of `store` must be called manually. To do this, import `store` from Storage and call the `dispatch` function, passing the desired action as an argument.

### Using connection
To make calls downstream use the API wrapping functions of `Downstream`. This queues a call to be sent downstream. When a response is received the given callback function is run. Since all error messages are formatted in a similar way, the handy function `callbackWrapper` has been implemented to reduce code duplication. The `callbackWrapper` function should be used to wrap all callbacks of API calls that can return errors (and no explicit error handling is going to be implemented).

### Using ColorWrapper
To use a custom color (in either theme or by hex-color directly) wrap a component in a `ColorWrapper`. This injects a local custom theme around the component, setting its color. **Note** that this somewhat diverges from the Material Design methodology, so use with care.

### Using TabDrawers
A `TabDrawer` consists of `TabDrawerTab`s. Each `TabDrawerTab` is added from the top and stacks downwards. The contents are contained in a list, meaning that `ListItem`s can be used directly as `TabDrawerTab` children. Each `TabDrawerTab` requires the property `icon` which defines the icon to be used in the tab head.

## Extension

### Extending components
Adding new components is straight forward. Create the desired React component and insert it into the product in any part of the inclusion tree. Extending existing components is just as easy. The code is generally structured in the following way: Component structure and style is generally kept in its own file, while functionality is given as a prop. For instance, the camera button is created and styled in `CameraButton` but its click handler is given to it by `Main`, where it is used.

### Extending storage
Storage is implemented with [Redux](https://redux.js.org/). To extend the Storage with another variable you need to add an Action, a Reducer, and mappings for state and dispatch. These are located in this order (from top to bottom) in the Storage file. The process can be quite involved to be sure to have a good understanding of Redux and especially the [React Redux](https://react-redux.js.org/) and [Redux Toolkit](https://redux-toolkit.js.org/) implementations. The following steps can be used to add a variable to Storage.

##### Action
To add an action constant use the React Toolkit function `createAction`. To note at this step is the addition of type checking to actions when run. This is done with a [prepare callback](https://redux-toolkit.js.org/api/createAction#using-prepare-callbacks-to-customize-action-contents). Good practice is to create a new object of the given argument, not only checking its contents. The prepare callback also allows for multiple arguments to be passed and handled.

##### Reducer
To add a reducer use the React Toolkit function `createReducer`. Here you give the default value of your Storage part. Note that each reducer is given a smaller portion of the entire `store` and reducers only modify this portion. When creating reducers the choice of writing them in either a mutating or non mutating style is given. In the current implementation all reducers are written in a non-mutating style. **Note** that even "mutating" styled reducers don't mutate the state directly, see more [here](https://redux-toolkit.js.org/api/createReducer#direct-state-mutation). Reducers are named the same as the eventual part of `store` they'll handle, prefixed with a "`_`". For instance `_sensorMode` for `store.sensorMode`.

##### Mappings
Two types of mappings needs to be added - a state mapping and a dispatch mapping. This boiler plate code insures that the final React component that gets connected to the Storage sees the Storage parts in a logical way.

Dispatch mappings can be written as functions or objects containing the desired actions. Add a dispatch mapping for your new actions. Creating constants for the groups of actions (see example in code) is not strictly needed, but is useful when importing.

State mappings can only be written as functions. Add a state mapping of your new `store` state. To emulate the behaviour of being able to map using an object, the higher order function `combineStateMappings` has been implemented to wrap these functions. This enables connecting of React components to state with the same syntax as for dispatch (with a wrapping of the React Redux connect function). To see an example and use of this, see the example in the `connect` function of Storage.

**Note** that these mappings that are the things that are imported and treated as states of the `store` by the React components, so the names given to these mappings is the name of the imported *"store state"*. To avoid confusion, keep the names of the mappings consistent with the mapping contents. 

##### Final touches
To have your new action and reducer be included in the default export from Storage, add your state mapping and dispatch mapping to the `states` and `actions` respectively.

The new reducer also needs to be added to the creation of the `store` object in the `configureStore` call at the bottom of the file.

### Extending connection
For each call of the downstream and upstream API there is a corresponding function of `Downstream` and `Upstream` respectively. These merely wrap the API-calls and generally don't add functionality. Functionality is added with the callback methods passed to the calls to these. When the API is extended, add a new corresponding wrapper function in either `Downstream` or `Upstream`.

## Future development

Here follows an overview of the future development goals for this product. See issues for more detailed descriptions.

 - [ ] Caching strategy for drone images (instead of reloading each image on view updates).
 - [ ] Change server connection behaviour to more robust.
 - [ ] Clean up Storage/split into multiple files.