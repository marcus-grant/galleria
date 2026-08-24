# Command Documentation

This directory contains detailed documentation for Galleria's
command-line interface.
Each command is documented with usage examples, options, and common
workflows.

## Available Commands

- **[process-photos](process-photos.md)** - Legacy photo processing.
  Superseded by NormPic; retained as a stub.
- **build** - Generate the static gallery from NormPic manifests.
- **serve** - Development server with reload for template work.

## Development Workflow

```bash
python -m galleria build
python -m galleria serve --reload
```

## Getting Help

For detailed help on any command:

```bash
python -m galleria COMMAND --help
```

For general help:

```bash
python -m galleria --help
```

## Contributing

When adding new commands, please:

1. Add documentation in this directory following the naming pattern
   `command-name.md`
2. Update this README with the new command
3. Include usage examples and common use cases
4. Document all CLI options and their purposes
