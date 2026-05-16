# SPDX-License-Identifier: Apache-2.0

CC=gcc
CFLAGS=-O2 -Wall -g

.PHONY: all

all: mouse_keyboard

mouse_keyboard: mouse_keyboard.c
	$(CC) -o $@ $< $(CFLAGS) -lpthread
