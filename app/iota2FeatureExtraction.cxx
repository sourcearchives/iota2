/*=========================================================================

  Program:   iota2
  Language:  C++

  Copyright (c) CESBIO. All rights reserved.

  See LICENSE for details.

  This software is distributed WITHOUT ANY WARRANTY; without even
  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
  PURPOSE.  See the above copyright notices for more information.

=========================================================================*/

#include "otbWrapperApplication.h"
#include "otbWrapperApplicationFactory.h"
#include "itkUnaryFunctorImageFilter.h"
#include "iota2FeatureExtraction.h"

namespace otb
{
namespace Wrapper
{

class iota2FeatureExtraction: public Application
{
public:
  typedef iota2FeatureExtraction Self;
  typedef Application                   Superclass;
  typedef itk::SmartPointer<Self> Pointer; 
  typedef itk::SmartPointer<const Self> ConstPointer;

  itkNewMacro(Self);
  itkTypeMacro(iota2FeatureExtraction, otb::Application);

  using FeatureExtractionFunctorType = 
    iota2::FeatureExtractionFunctor<typename FloatVectorImageType::PixelType>;
  using FeatureExtractionFilterType = 
    iota2::UnaryFunctorImageFilterWithNBands<FloatVectorImageType, 
                                             FloatVectorImageType, 
                                             FeatureExtractionFunctorType>;  

private:
  void DoInit()
  {
    SetName("iota2FeatureExtraction");
    SetDescription("Feature extraction for iota2.");

    // Documentation
    SetDocName("Feature extraction");
    SetDocLongDescription("This application performs .");
    SetDocLimitations("None");
    SetDocAuthors("Jordi Inglada");

    AddDocTag(Tags::Filter);
    AddDocTag("MultiTemporal");
    
    AddParameter(ParameterType_InputImage,  "in",   "Input time series");
    SetParameterDescription("in", "Input time series");
    MandatoryOn("in");

    AddParameter(ParameterType_OutputImage, "out",  "Output time series");
    SetParameterDescription("out", "Output time series");
    MandatoryOn("out");

    AddParameter(ParameterType_Int, "comp", "Number of components per date.");

    AddParameter(ParameterType_Int, "red", 
                 "Index for the red band (starting at 1).");
    AddParameter(ParameterType_Int, "nir", 
                 "Index for the NIR band (starting at 1).");
    AddParameter(ParameterType_Int, "swir", 
                 "Index for the SWIR band (starting at 1).");
    AddParameter(ParameterType_Float, "indfact", 
                 "Multiplicative factor for nomalized indices (default = 1000).");
    MandatoryOff("indfact");
    AddParameter(ParameterType_Float, "nodata", 
                 "No data value (default = -10000).");
    MandatoryOff("nodata");

    AddParameter(ParameterType_Empty, "copyinput", "Copy input bands to output image (true/false). Default value is false");
    MandatoryOff("copyinput");

    AddRAMParameter();
  }

  void DoUpdateParameters()
  {
  }

  void DoExecute()
  {  
    auto cpd = 1;
    if(IsParameterEnabled("comp"))
      cpd = GetParameterInt("comp");
    auto redIndex = 3;
    if(IsParameterEnabled("red"))
      redIndex = GetParameterInt("red");
    auto nirIndex = 4;
    if(IsParameterEnabled("nir"))
      nirIndex = GetParameterInt("nir");
    auto swirIndex = 5;
    if(IsParameterEnabled("swir"))
      swirIndex = GetParameterInt("swir");
    auto normIndexFactor = float{1000};
    if(IsParameterEnabled("indfact"))
      normIndexFactor = GetParameterInt("indfact");
    auto noDataValue = float{-10000};
    if(IsParameterEnabled("nodata"))
      noDataValue = GetParameterInt("nodata");
    auto copyInputBands = false;
    if (IsParameterEnabled("copyinput"))
      {
      copyInputBands = true;
      }

    std::cout << "Copy input is " << copyInputBands << "\n";
    FloatVectorImageType::Pointer inputImage = this->GetParameterImage("in");
    inputImage->UpdateOutputInformation();
    auto nbOfInputBands = inputImage->GetNumberOfComponentsPerPixel();
    auto fef = FeatureExtractionFunctorType(cpd,
                                            redIndex,
                                            nirIndex,
                                            swirIndex,
                                            normIndexFactor,
                                            noDataValue,
                                            nbOfInputBands,
                                            copyInputBands);
    m_FeatureExtractionFilter = FeatureExtractionFilterType::New();
    m_FeatureExtractionFilter->SetFunctor(fef);
    m_FeatureExtractionFilter->SetInput(inputImage);
    m_FeatureExtractionFilter->SetNumberOfOutputBands(fef.GetNumberOfOutputComponents());
    SetParameterOutputImage("out", m_FeatureExtractionFilter->GetOutput());
  }

  FeatureExtractionFilterType::Pointer m_FeatureExtractionFilter;
};
} // end namespace Wrapper
} // end namespace otb

OTB_APPLICATION_EXPORT(otb::Wrapper::iota2FeatureExtraction)
