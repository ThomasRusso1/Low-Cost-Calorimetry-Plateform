# Low-Cost-Calorimetry-Plateform
This repository introduces the low-cost calorimetry platform I have developed at the University of Minho (Portugal) in the framework of my PhD thesis. This platform allows to conduct isothermal and adiabatic calorimetry with lab-grade accuracy, as well as DSC applications. Each of the calorimetry modes can be seen as a module; the electronic hardware and software is the same for all applications. The extensive validation process can be found in my thesis, which I will refer to once published.
The calorimetric cells allowing for heat flux monitoring for isothermal and DSC applications have been made from off-the-shelf components easily available regular hardware and electronic stores. The adiabatic module is represented by a soil permeability test mould; however, water-tight container with cable-pass and an internal volume of around 2L can do the job.
The description of the BoM, CAD parts, Assembly, and different codes required can be found in the various files of this repository.
<img width="707" height="415" alt="image" src="https://github.com/user-attachments/assets/5251797d-ede7-4dd9-877c-826f2cc288e1" />

1. **Get the components:** Get the different components, which you can find in [click for BoM](Hardware/BoM.csv)
2. **Electronic assembly:** Assemble and connect the electronic components as in the diagram presented in [click for interaction diagram](Hardware/images/Components_interaction_diagram.png). Connect the Peltier cells to the Linduino. 
3. **Create your calorimetric cells:** Follow the steps from [click for steps](Hardware/assembly_steps.md) to create your calorimetric cells.
4. **Adiabatic module:** Find or make the adequate water-tight container to create your adiabatic module, like in [click for adiabatic module](Hardware/images/Adiabatic_module_pictures.png)
5. **Enjoy your lab-grade calorimetry platform!** Enjoy, don't hesitate to contribute and if you have any question feel free to ask.
