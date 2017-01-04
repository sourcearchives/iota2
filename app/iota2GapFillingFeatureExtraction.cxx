/*=========================================================================

  Program:   gapfilling
  Language:  C++

  Copyright (c) Jordi Inglada. All rights reserved.

  See LICENSE for details.

  This software is distributed WITHOUT ANY WARRANTY; without even
  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
  PURPOSE.  See the above copyright notices for more information.

=========================================================================*/

#include "otbWrapperApplication.h"
#include "otbWrapperApplicationFactory.h"
#include "otbWrapperApplicationRegistry.h"

namespace otb
{
namespace Wrapper
{

class GapFillingFeatureExtraction: public Application
{
public:
  typedef GapFillingFeatureExtraction Self;
  typedef Application                   Superclass;
  typedef itk::SmartPointer<Self> Pointer; 
  typedef itk::SmartPointer<const Self> ConstPointer;

  itkNewMacro(Self);
  itkTypeMacro(GapFillingFeatureExtraction, otb::Application);  

private:
  void DoInit()
  {
    SetName("GapFillingFeatureExtraction");
    SetDescription("Time series gapfilling.");

    // Documentation
    SetDocName("Image Time Series Gap Filling");
    SetDocLongDescription("This application performs .");
    SetDocLimitations("None");
    SetDocAuthors("Jordi Inglada");

    AddDocTag(Tags::Filter);
    AddDocTag("MultiTemporal");
    
    AddParameter(ParameterType_InputImage,  "in",   "Input time series");
    SetParameterDescription("in", "Input time series");
    MandatoryOn("in");

    AddParameter(ParameterType_InputImage,  "mask",   "Mask time series");
    SetParameterDescription("mask", "Input validity time series mask");
    MandatoryOn("mask");

    AddParameter(ParameterType_OutputImage, "out",  "Output time series");
    SetParameterDescription("out", "Output time series");
    MandatoryOn("out");

    AddParameter(ParameterType_Int, "comp", "Number of components per date.");
    AddParameter(ParameterType_String, "it", 
                 "Interpolation type (linear, spline)");
    AddParameter(ParameterType_String, "id", 
                 "Input date file");
    MandatoryOff("id");
    AddParameter(ParameterType_String, "od", 
                 "Output date file");
    MandatoryOff("od");

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

  }

  void DoUpdateParameters()
  {
  }

  void DoExecute()
  {  
    m_GapFillingApp = ApplicationRegistry::CreateApplication("ImageTimeSeriesGapFilling");
    m_GapFillingApp->SetParameterInputImage("in", this->GetParameterImage("in"));
    m_GapFillingApp->SetParameterInputImage("mask", this->GetParameterImage("mask"));
    m_GapFillingApp->SetParameterInt("comp", this->GetParameterInt("comp"));
    m_GapFillingApp->SetParameterString("it", this->GetParameterString("it"));
    m_GapFillingApp->SetParameterString("id", this->GetParameterString("id"));
    m_GapFillingApp->SetParameterString("od", this->GetParameterString("od"));
    m_GapFillingApp->Execute();

    m_FeatextrApp = ApplicationRegistry::CreateApplication("iota2FeatureExtraction");
    m_FeatextrApp->SetParameterInputImage("in", m_GapFillingApp->GetParameterOutputImage("out"));
    m_FeatextrApp->SetParameterInt("comp", this->GetParameterInt("comp"));
    m_FeatextrApp->SetParameterInt("red", this->GetParameterInt("red"));
    m_FeatextrApp->SetParameterInt("nir", this->GetParameterInt("nir"));
    m_FeatextrApp->SetParameterInt("swir", this->GetParameterInt("swir"));
    m_FeatextrApp->SetParameterFloat("indfact", this->GetParameterFloat("indfact"));
    m_FeatextrApp->SetParameterFloat("nodata", this->GetParameterFloat("nodata"));
    m_FeatextrApp->Execute();

    SetParameterOutputImage("out", m_FeatextrApp->GetParameterOutputImage("out"));
  }

  Application::Pointer m_GapFillingApp;
  Application::Pointer m_FeatextrApp;

};
} // end namespace Wrapper
} // end namespace otb

OTB_APPLICATION_EXPORT(otb::Wrapper::GapFillingFeatureExtraction)
