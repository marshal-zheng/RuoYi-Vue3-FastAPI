# Schema package release-closeout snapshot

The post dialog consumes `@zxio/schema-form/form-create` through
`zxio-schema-form-0.1.0-closeout.20261019.tgz`. The identical tarball is used by
x6-devkit. The filename suffix identifies local acceptance; the package version
is `0.1.0`. It is built from ZXUI `packages/schema-form/dist`, including public
JS/types/style, README and LICENSE. Runtime files match the previously accepted
pilot byte for byte.

The application explicitly installs `@form-create/element-ui@3.3.5` for this
optional facet. Vue, Element Plus and ZXUI are host peers. The schema package
never owns HTTP requests, post identity/DTOs, dictionary loading or dialog closure.

Keep the current ZXUI and theme-compiler snapshots: they contain the public field
and source-plugin changes needed by this consumer. Other Dashboard/HTTP/theme
snapshots belong to their respective deliveries and are not cleanup candidates.
`VITE_ZXUI_LOCAL=true` with an explicit `VITE_ZXIO_REPO_ROOT` remains the supported
source-debugging path; normal production builds use locked package dependencies.

After the corresponding packages are authorized and published, upgrade the
compatible ZXUI/theme packages, replace schema-form's file dependency with its
published `0.1.0`, and regenerate `yarn.lock`. Verify typecheck, post regressions,
production build and the real post page before removing the replaced snapshots.
Do not substitute registry versions merely because their version numbers match
an unpublished local snapshot.
