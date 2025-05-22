# Learn Vibe Programming Language

Welcome to the Vibe Programming Language! This guide will help you get started with Vibe, a simple and expressive programming language.

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Basic Syntax](#basic-syntax)
4. [Examples](#examples)
5. [Advanced Features](#advanced-features)
6. [Resources](#resources)

## Introduction

Vibe is a programming language designed for simplicity and expressiveness. It supports both interpreted and compiled execution, making it versatile for various use cases.

## Getting Started

### Requirements

- Python 3.6+
- GCC toolchain (for compilation)
- ARM64 assembler (as)
- LLVM toolchain (for LLVM backend)

### Installation

Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/your-repo/vibe.git
cd vibe
```

## Basic Syntax

### Variables

Assign values to variables using the `➡️` operator:

```vibe
name ➡️ "World"
```

### Print Statements

Use the `holla` keyword to print messages:

```vibe
holla "Hello, World!"
```

### String Operations

Concatenate strings using the `+` operator:

```vibe
holla "Hello, " + name
```

## Examples

### Hello World

```vibe
// This is our first Vibe program
name ➡️ "World"
holla "Hello " + name
```

### Simple Math

```vibe
x ➡️ 10
y ➡️ 20
holla "Sum: " + (x + y)
```

### Conditional Statements

```vibe
x ➡️ 10
if x > 5 {
    holla "x is greater than 5"
} else {
    holla "x is 5 or less"
}
```

## Advanced Features

### Compilation

Compile a Vibe program to an executable:

```bash
./vibe compile program.vpl -o program
```

### Interpreter

Run a Vibe program directly:

```bash
./vibe run program.vpl
```

### Backends

Choose a backend for compilation:

- `native`: ARM64 assembly
- `simple`: Simplified ARM64 assembly
- `llvm`: LLVM IR

## Resources

- [GitHub Repository](https://github.com/your-repo/vibe)
- [Documentation](https://your-docs-site.com/vibe)
- [Community Forum](https://forum.your-site.com/vibe)
