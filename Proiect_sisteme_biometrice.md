
# Anti biometric keystroke profiling project ##

### Students: Cosmin Ciobanu, Razvan Gavrila

## Requirements
** Linux driver for modifying the keystrokes flight & dwell time **

#### The program in detail:

Main methods of the program:

This method prints out the timestamp and key code of a Key Event


```python
void KeyEventRead(struct input_event ev)
{
    printf(KRED "\nEVENT READ\n" KNRM);
    printf("Timestamp: %ld.%06ld \n", ev.time.tv_sec, ev.time.tv_usec);
    printf("Key code: %d \n", ev.code);
}
```

When a key is pressed:
  - print out the time passed since the previous key event
  - inject some random microseconds to disable fingerprinting
  - check if the current key is CTRL to set a stand by state for the next key
  - if next key is Q, CTRL+Q was pressed and the program exits


```python
int KeyPressed(struct input_event ev, struct timeval t1, struct timeval t2, int status)
{
    printf(KGRN "\nKEY PRESSED \n" KNRM);
    printf("Elapsed time since previous key: %ld.%6ld \n", t1.tv_sec - t2.tv_sec, t1.tv_usec - t2.tv_usec);
    int r = (500 + rand() % 500);
    sleep(r/1000);
    printf("Injected %d milliseconds between keys \n", r);
    if (ev.code == EXIT_KEY1){
        printf("CTRL pressed: waiting for Q... \n");
    return 1;
    }
    if (status == 1){
        if (ev.code == EXIT_KEY2){
            printf("\nExiting... \n");
            printf("Bye bye\n");
            return 2;
        }
    }
    return 0;
}

```

When key is released:
- print time passed since key event was triggered
- inject random microseconds to disable fingerprinting


```python
void KeyReleased(struct timeval t1, struct timeval t2)
{
    printf(KCYN "\nKEY RELEASED\n" KNRM);
    printf("Time since key was pressed: %ld.%6ld \n", t2.tv_sec - t1.tv_sec, t2.tv_usec - t1.tv_usec);
    int r = (500 + rand()%500*100);
    usleep(r);
    printf("Injected %d miliseconds after release \n", r/100);
}
```

Ref 1: Getting started with uinput by Gregory Thiemonge
http://thiemonge.org/getting-started-with-uinput

Ref 2: Linux Corss Reference
http://lxr.free-electrons.com/ident?i=EVIOCGRAB

Try to access input device to grab events (MitM) via the EVIOCGRAB-ioctl call
EVICGRAB is used to grab and release a device and is part of input.h in the linux kernel


```python
int InputInit(char* inputDevice)
{
    int fdi;
    fdi = open(inputDevice, O_RDONLY);
    if(fdi < 0) ExitProgram("Error: while opening input device");
    if(ioctl(fdi, EVIOCGRAB, 1) < 0) ExitProgram("Error: unable to access EVIOCGRAB");
    return fdi;
}
```

Ref 1: Getting started with uinput by Gregory Thiemonge
http://thiemonge.org/getting-started-with-uinput

Ref 2: Linux Kernel (GitHub)
https://github.com/torvalds/linux/blob/master/include/uapi/linux/input.h
https://github.com/torvalds/linux/blob/master/include/uapi/linux/input-event-codes.h

Ref 3: Event codes
https://www.kernel.org/doc/Documentation/input/event-codes.txt

- access the uinput kernel module that allows us to access the input subsystem.
- uinput should be accessed n write-only and non-blocking mode
- we set which type of events we are interested in (defined in linux/input.h)
- we will capture EV_SYN (used as markers to separate event), EV_KEY (used to describe
  state changes of keyboards) and EV_MSC(used to describe relative axis value changes)
- we create a new input device with the name of AntiBiometric-Keyboard


```python
int OutputInit()
{
    struct uinput_user_dev uidev;
    const char* ioctl_error = "Error: while accessing Input-Output Control";
    int fdo;

    fdo = open("/dev/uinput", O_WRONLY | O_NONBLOCK);
    if(fdo < 0) ExitProgram("Error: unable to open uniput module");
    if(ioctl(fdo, UI_SET_EVBIT, EV_SYN) < 0) ExitProgram(ioctl_error);
    if(ioctl(fdo, UI_SET_EVBIT, EV_KEY) < 0) ExitProgram(ioctl_error);
    if(ioctl(fdo, UI_SET_EVBIT, EV_MSC) < 0) ExitProgram(ioctl_error);

    for(int i = 0; i < KEY_MAX; ++i)
        if(ioctl(fdo, UI_SET_KEYBIT, i) < 0) ExitProgram(ioctl_error);

    memset(&uidev, 0, sizeof(uidev));
    snprintf(uidev.name, UINPUT_MAX_NAME_SIZE, "AntiBiometric-Keyboard");
    uidev.id.bustype = BUS_USB;
    uidev.id.vendor  = 0x1;
    uidev.id.product = 0x1;
    uidev.id.version = 1;

    if(write(fdo, &uidev, sizeof(uidev)) < 0) ExitProgram("Error: unable to create new input device");
    if(ioctl(fdo, UI_DEV_CREATE) < 0) ExitProgram(ioctl_error);
    return fdo;
}

```
- print out the event using our new input device

```python
void KeyPrint(int fdo, struct input_event ev)
{
    ev.time.tv_sec = 0;
    ev.time.tv_usec = 0;

    if(write(fdo, &ev, sizeof(struct input_event)) < 0)
            ExitProgram("Error: while writing event");
}

```
- main routine 

```python
int main(int argc, char* argv[])
{
    int    fdo, fdi;
    struct input_event ev;
    int    status, buff;
    struct timeval t1, t2;

    if(argc != 2)
        ExitProgram("Error: No input device specified. \nTry /dev/input/event0 \n");

    fdi = InputInit(argv[1]);
    fdo = OutputInit();

    gettimeofday(&t2, NULL);

    CoolBanner();

    status = 0;

    while(!done)
    {
        // read input event
        if(read(fdi, &ev, sizeof(struct input_event)) < 0)
            ExitProgram("Error: while reading event");

        // check if it was a key event
        if (ev.type == EV_KEY){
            KeyEventRead(ev);

            // if key was pressed check if user is attempting LCTRL + Q
            // run KeyPressed()

            if (ev.value == KEY_PRESSED){
                gettimeofday(&t1, NULL);
                status = KeyPressed(ev, t1, t2, status);
                if (status == 2)
                    done=true;
            }

            // if key was released run KeyReleased()

            if (ev.value == KEY_RELEASED){
                gettimeofday(&t2, NULL);
                KeyReleased(t1, t2);
            }
        }

        // send event to our input device

        KeyPrint(fdo, ev);
    }

    // Destroy new input device as we are done
    if(ioctl(fdo, UI_DEV_DESTROY) < 0) ExitProgram("Error: while accessing Input-Output Control");
    close(fdi);
    close(fdo);
    return 0;
}
```
