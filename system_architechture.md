# The OSI Model
The OSI model which stands for Open Systems Interconnection is a 7 layer refrence model that is used to describe how data flows across a network. It was designed by the ISO to create a standard for network but it is a conceptual model and not a practical one.

## The Layers
The OSI model comprises of 7 seperate layers:
1. __Application Layer__ - this is the layer the user interects with directly like browsers, email clients etc. This is the point at which data is either generated or consumed.

2. __Presentation Layer__ - This layer handles formatting, encryption and compression so data from one system can be understood by another.

3. __Session Layer__ - This layer manages the opening, maintaining and closing of a communication session between two devices.

4. __Transport Layer__ - The transport layer is responsible for the reliable or unreliable delivery of data. TCP (Transmmission Control Protocol) and UDP (User Datagram Protocol) operate at this layer conceptually.

5. __Network Layer__ - This layer handles logical addressing and routing, this is where IP addresses and routing decisions happen.

6. __Data Link Layer__ - This is responsible framing data for transmission on the physical medium and handles MAC (Media Access Control) addressing.

7. __Physical Layer__ - This involves the actual transmission of raw bits as electrical signals, light pulses or radio waves over the physical medium.

![OSI model Diagram](https://res.cloudinary.com/dwinqwsit/image/upload/v1784803778/osi_model_7_layers_ycdkyc.png)

## Why the OSI model isn't used Practically
Athough the OSI model is the standard networking reference, real networks use the ***TCP/IP*** model because it was developed earlier and widely adoped before the OSI model was completed. TCP/IP was simple and it had already been proven to work.

> The OSI model is mainly used for learning and troubleshooting networks, while the TCP/IP is the model actually used to design and build networks.

## The Practical Model: __TCP/IP__
The TCP/IP model is what real world networks are built on. In compacts the & layers of the OSI model into 4 distinct layers:

1. __Application Layer__ - This combines the OSI's Application, Presentation and Session layers. Protocols such as ___HTTPS___ (Hyper Text Transfer Protocol), ___DNS___ (Domain Name System), ___FTP___ (File Transfer Protocol) and ___SMTP___ (Simple Mail Transfer Protocol) operate here and applications handles their own formatting and session management.

2. __Transport Layer__ - It is equivalent to the ___OSI___ Transport Layer. ___TCP___ provides reliable, connection oriented delivery while ___UDP___ provides faster, connectionless delivery without the guarantee of delivery.

3. __Internet Layer__ - It translates to the ___OSI___ Network Layer. It is responsible for IP addressing and routing between networks.

4. __Network Access Layer__ - It combines the ___OSI's___ Data Link and Physical Layers which covers both the framing of data and its actual transmission over hardware.
![TCP?IP model diagram](https://res.cloudinary.com/dwinqwsit/image/upload/v1784803775/16_A1-Digital-TCP-IP-Model-layers-explained_v2_zhgusz.jpg)

![Model Comparism](https://res.cloudinary.com/dwinqwsit/image/upload/v1784803776/stock-vector-colorful-osi-and-tcp-ip-model-comparison-diagram-2691349351_agjzcp.jpg)

# System Architechture: What happens when you perform an action

## Step 1: Input Generation
When you perform an action such as a mouse click or keystoke, those actions are converted into an electrical signal by the input devices's internal controller. The signal is transmitted to the system through an interface such as a usb.

## Step 2: Interrupt Handling
The ___CPU___ doesn't just stay polling the input devices, that would waste processing power. What happens instead is that when the devices sends its signal, it raises an interrupt. This tells the ___CPU___ to pause whatever it is currently processing, save the state of the current program executing, pushes it to the stack and then jumps to a part of the kernel code called an interrupt handler.

## Step 3: Kernel-Level Processing
The device driver, which runs inside the kernel, reads the raw data sitting insdie the device buffer. It then converts this raw data into something the system can actually use.

## Step 4: Event Routing
Since many programs can be running at the same time, the kernel needs to know whcih one should receive this event. The scheduler works together with thhe window manager (X11 or Wayland for linux) to check which window currently has focus and the event is sent to that window's process

## Step 5: Context Switch
Before the target process can respond to the event, the kernel performs a context switch. This means it saves the current statw of whatever process was running and loads the state of the process that needs to handle the click.

## Step 6:  Memory Addressing
The ___MMU___ (Memory Management Unit) translates virtual addresses used by the process into physical address in RAM based on page tables maintained by the kernel.

Depending on the instruction being executed, the CPu may use different addressing modes to access data:

> __Immediate Addressing__ - The operand value is contained directly within the instruction.

> __Direct Addressing__ - The instruction specifies the exact memory address of the operand.

> __Register Addressing__ - The operand is located in a CPU register, allowing the fastest access since no memory access is required.

> __Indirect/Indexed Addressing__ - The instruction contains a pointer to the actual address, commonly used for arrays and dynamic data structures.

## Step 7: FED Ccyle
Once the process resumes, the CPu begins running its instructions through the fetch-decode-execute cycle. First it fetches the next instruction from memory using the ___Program Counter___. Then it decodes the instruction to understand what operation it is asking for. Finally it executes the instruction.

## Step 8: Application Logic 
The application itself now runs the code attached to that event, usually through an event loop or a callback function.

## Step 9: Rendering
Any visual change is passed to the graphics stack through a graphics api as OpenGL, Vulkan, DirectX or Metal, depending on the system. The ___GPU___ takes this information and renders the new frame into a frame buffer.

## Step 10: Display Composition
The display manager or compositor takes that rendered frame and combines it with everything else currently on screen such as other open windows, other elements on the gui. Once combined, the final frame is sent out through a display interface like HDMI, VGA etc

## Step 11: Final Output
The screen displays the frame and the result of the action that was taken is seen.

![System Arch diagram](https://res.cloudinary.com/dwinqwsit/image/upload/v1784804804/file_00000000d4a881f48c7db8504ed05fbb_bp1ivg.png)
