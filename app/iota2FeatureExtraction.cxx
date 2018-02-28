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
  void DoInit() override
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
                 "Multiplicative factor for normalized indices (default = 1000).");
    MandatoryOff("indfact");
    AddParameter(ParameterType_Float, "nodata", 
                 "No data value (default = -10000).");
    MandatoryOff("nodata");

    AddParameter(ParameterType_Empty, "copyinput", "Copy input bands to output image (true/false). Default value is false");
    MandatoryOff("copyinput");

    AddParameter(ParameterType_Empty, "relrefl", "Compute relative reflectances (true/false). Default value is false");
    MandatoryOff("relrefl");

    AddParameter(ParameterType_Int, "relindex", "Index for the band used as reference reflectance (starting at 1). The red band is used by default");
    MandatoryOff("relindex");

    AddParameter(ParameterType_Empty, "keepduplicates", "Keep duplicate relative reflectances (true/false). Default value is false");
    MandatoryOff("keepduplicates");



    AddRAMParameter();
  }

  void DoUpdateParameters() override
  {
  }

  void DoExecute() override
  {  
    auto pars = FeatureExtractionFunctorType::Parameters{};

    FloatVectorImageType::Pointer inputImage = this->GetParameterImage("in");
    inputImage->UpdateOutputInformation();
    pars.NumberOfInputComponents = inputImage->GetNumberOfComponentsPerPixel();

    if(IsParameterEnabled("comp"))
      pars.ComponentsPerDate = GetParameterInt("comp");
    if(IsParameterEnabled("red"))
      pars.RedIndex = GetParameterInt("red");
    if(IsParameterEnabled("nir"))
      pars.NIRIndex = GetParameterInt("nir");
    if(IsParameterEnabled("swir"))
      pars.SWIRIndex = GetParameterInt("swir");
    if(IsParameterEnabled("indfact"))
      pars.NormalizedIndexFactor= GetParameterInt("indfact");
    if(IsParameterEnabled("nodata"))
      pars.NoDataValue= GetParameterInt("nodata");
    if (IsParameterEnabled("copyinput"))
      {
      pars.CopyInputBands = true;
      }
    if(IsParameterEnabled("relrefl"))
      {
      std::cout << " Relative reflectances \n";
      pars.RelativeReflectances = true;
      if(IsParameterEnabled("keepduplicates") || pars.CopyInputBands==false)
        {
        std::cout << " keep duplicates \n";
        pars.RemoveDuplicates = false;
        }
      if(IsParameterEnabled("relindex"))
        {
        pars.ReferenceIndex = GetParameterInt("relindex");
        if(pars.ReferenceIndex > pars.ComponentsPerDate)
          {
          itkExceptionMacro(<<"relindex must be between 1 and the number of components per date\n");
          }
        }
      std::cout << " relative index " << pars.ReferenceIndex << " \n";
      }

    
    auto fef = FeatureExtractionFunctorType(pars);
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
