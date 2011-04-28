#                                               -*- Autoconf -*-
# Process this file with autoconf to produce a configure script.

AC_PREREQ([2.65])
AC_INIT([gant], [0.5], [wwb2@cornell.edu])
AM_INIT_AUTOMAKE([gant], [0.5])
AC_CONFIG_SRCDIR([antlib.c])
#AC_CONFIG_HEADERS([config.h])

# Checks for programs.
AC_PROG_CC

# Checks for header files.
AC_CHECK_HEADERS([fcntl.h stdlib.h string.h sys/time.h termios.h unistd.h])

# Checks for typedefs, structures, and compiler characteristics.
AC_TYPE_SSIZE_T

# Checks for library functions.
AC_FUNC_MALLOC
AC_FUNC_REALLOC
AC_CHECK_FUNCS([bzero floor gettimeofday memmove memset select])

AC_CONFIG_FILES([Makefile])
AC_OUTPUT


