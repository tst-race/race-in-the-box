# RiB UI React App

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

This project follows many of the conventions and recommendations from
[Bulletproof React](https://github.com/alan2207/bulletproof-react).

## Project Structure

Following the convention from Bulletproof React, the `src` directory is
arranged as follows (to the extent it is applicable):

```sh
src
|
+-- assets            # assets folder can contain all the static files such as images, fonts, etc.
|
+-- components        # shared components used across the entire application
|
+-- config            # all the global configuration, env variables etc. get exported from here and used in the app
|
+-- features          # feature based modules
|
+-- hooks             # shared hooks used across the entire application
|
+-- lib               # re-exporting different libraries preconfigured for the application
|
+-- providers         # all of the application providers
|
+-- routes            # routes configuration
|
+-- stores            # global state stores
|
+-- test              # test utilities and mock server
|
+-- types             # base types used across the application
|
+-- utils             # shared utility functions
```

Features have the following structure (to the extent it is applicable):

```sh
src/features/some-feature
|
+-- api         # exported API request declarations and api hooks related to a specific feature
|
+-- assets      # assets folder can contain all the static files for a specific feature
|
+-- components  # components scoped to a specific feature
|
+-- hooks       # hooks scoped to a specific feature
|
+-- routes      # route components for a specific feature pages
|
+-- stores      # state stores for a specific feature
|
+-- types       # typescript types for TS specific feature domain
|
+-- utils       # utility functions for a specific feature
|
+-- index.ts    # entry point for the feature, it should serve as the public API of the given feature and exports everything that should be used outside the feature
```

Everything from a feature is exported from the `index.ts` file which behaves as
the public API of the feature.

Anything imported from a feature can only be done using:

`import { SomeComponent } from '@/features/some-feature`

and not

`import { SomeComponent } from '@/features/some-feature/components/SomeComponent`

This is enforced by the ESLint configuration.

### Feature Modules

The following are the features that exist in this project:

```sh
src/features
|
+-- config          # global RiB configuration
|
+-- deployments     # deployment creation, operations, and statusing
|
+-- range-config    # range-config generation
```

## Project-specific Design Decisions

The following are design or implementation decisions that did not necessarily
come from Bulletproof React:

### Blueprint Component Library

The project uses the [Blueprint](https://blueprintjs.com/docs/) component
library. There are many custom components and some custom styling of the
Blueprint components, but Blueprint provides all the foundational components
(e.g., buttons, dialogs).

### CSS Modules

Component styling is done using [CSS Modules](https://github.com/css-modules/css-modules).

### Query Keys

We are using [React Query](https://react-query-v3.tanstack.com/overview) for all
API requests. All request functions are defined along with hooks in `api/`
folders in their respective features.

Following the advice from [Effective React Query Keys](https://tkdodo.eu/blog/effective-react-query-keys),
we centralize all the query keys for a feature's API calls in a `api/queryKeys.ts`
file for each feature.

### Request Mocking

In unit tests, all API calls are mocked out using [mock service worker](https://mswjs.io/docs/).

We can also use msw to mock out API calls made by the app running in the browser.
To start the development app with mocking, run `npm run start:mock`. All mocked
responses are defined in the `src/test/server/handlers.ts` file.

### API Schema Tests

In order to ensure compatibility between the backend APIs and the frontend API
requests, we perform schema compliance validation against our defined types as
part of unit tests.

The API schema must be located at `src/test/openapi.json` in order for the tests
to work. To generate this file locally, run the `scripts/internal/generate_openapi_spec.py`
script. In CI, we generate the OpenAPI spec file in the build stage, then copy
that artifact into the unit test stage.

See `src/features/config/types/schemas.test.ts` for an example.

## Available Scripts

In the `webapp` directory, you can run:

### `npm ci`

Installs all version-pinned NPM dependencies.

### `npm run start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

The page will reload if you make edits.\
You will also see any lint errors in the console.

### `npm run start:mock`

Runs the app in the development mode with mocked API requests responses.\
Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

The page will reload if you make edits.\
You will also see any lint errors in the console.

### `npm run test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

### `npm run lint`

Runs ESLint validation against all source code.\
It will exit with a non-zero exit code if any errors are found.

### `npm run lint:fix`

Runs ESLint to modify source code and fix all auto-fixable linting errors.

### `npm run prettier`

Runs prettier to modify and auto-format source code.

### `npm run check-types`

Runs the TypeScript compiler to validate types.

### `npm run validate`

Performs the `check-types` and `lint` operations in parallel.

### `npm run storybook`

Runs the storybook app.\
Open [http://localhost:6006](http://localhost:6006) to view it in the browser.

The page will reload if you make edits.

See [storybook.js.org](https://storybook.js.org/docs/react/get-started/introduction) for more information.

### `npm run build-storybook`

Builds a static version of the storybook app.
