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
#include "itkBinaryFunctorImageFilter.h"
#include "extractSortedIndices.h"
#include "otbDateUtils.h"

namespace otb
{
namespace Wrapper
{
class extractSortedIndices: public Application
{
public:
typedef extractSortedIndices Self;
typedef Application Superclass;
typedef itk::SmartPointer<Self> Pointer;
typedef itk::SmartPointer<const Self> ConstPointer;

itkNewMacro(Self);
itkTypeMacro(extractSortedIndices,otb::Application);

using TPixel = typename FloatVectorImageType::PixelType;
using TValue = typename TPixel::ValueType;

using extractSortedIndicesWithMask_Functor =
ESI::FeatureExtractionWithMaskFunctor<typename  FloatVectorImageType::PixelType>;
using extractSortedIndicesWithMask_Filter =
ESI::BinaryFunctorImageFilterWithNBands<FloatVectorImageType,FloatVectorImageType,FloatVectorImageType,
                                       extractSortedIndicesWithMask_Functor>;
private:
  void DoInit() override
  {
  SetName("extractSortedIndices");
  SetDescription("from a stack, return index's Band sorted");
  SetDocLongDescription("This application performs ...");
  SetDocLimitations("None");
  SetDocAuthors("Arthur VINCENT");
  AddDocTag(Tags::Filter);
  AddDocTag("MultiTemporal");

  AddParameter(ParameterType_InputImage,"in","Input time series");
  SetParameterDescription("in","Input time series");
  SetDocExampleParameterValue("in","My_NDVI_time_serie.tif");
  MandatoryOn("in");

  AddParameter(ParameterType_InputImage,"mask","Mask time series");
  SetParameterDescription("mask","Input validity time series mask");
  SetDocExampleParameterValue("mask","My_MASK_time_serie.tif");
  MandatoryOn("mask");

  AddParameter(ParameterType_String,"id","Input file date time format(YYYYMMDD)");
  SetParameterDescription("id","acquisition date time format(YYYYMMDD)");
  SetDocExampleParameterValue("id","/path/to/input_dates.txt");
  MandatoryOn("id");

  AddParameter(ParameterType_Choice,"mode","determine output's dimension");
  SetParameterDescription("mode","determine output's dimension");
  SetDocExampleParameterValue("mode","fix");

  AddChoice("mode.asinput","output=input component");
  AddChoice("mode.auto","output = min dimension component");
  AddChoice("mode.fix","output = user request component");
  MandatoryOff("mode.asinput");
  MandatoryOff("mode.auto");
  MandatoryOff("mode.fix");

  AddParameter(ParameterType_Int,"mode.fix.comp","number of output bands");
  SetDocExampleParameterValue("mode.fix.comp","5");
  SetMinimumParameterIntValue("mode.fix.comp",0);
  MandatoryOff("mode.fix.comp");

  MandatoryOff("mode");

  AddParameter(ParameterType_OutputImage,"out","Output");
  SetParameterDescription("out","Output");
  SetDocExampleParameterValue("out","output.tif");
  MandatoryOn("out");
  }
  void DoUpdateParameters() override
  {} 
  void DoExecute() override
  {
   auto pars = extractSortedIndicesWithMask_Functor::Parameters{};
   FloatVectorImageType::Pointer inputImage = this->GetParameterImage("in");
   FloatVectorImageType::Pointer mask = this->GetParameterImage("mask");
   
   size_t inBandsNumber = inputImage->GetNumberOfComponentsPerPixel();
   size_t maskBandsNumber = mask->GetNumberOfComponentsPerPixel();
   size_t nbOutComp = inBandsNumber;
   if (IsParameterEnabled("mode"))
     std::string mode = this->GetParameterString("mode");
   if(this->GetParameterString("mode") == "fix")
     {
       std::cout<<"ICIIIIII";
     nbOutComp = this->GetParameterInt("mode.fix.comp");
     }
   TPixel dv;

   std::string in_date_file{""};
   in_date_file = GetParameterString("id");
   auto date_vec = GapFilling::parse_date_file(in_date_file);
   std::vector<TValue> doy_vector(date_vec.size(),TValue{0});
   std::transform(std::begin(date_vec),std::end(date_vec),std::begin(doy_vector),GapFilling::doy_multi_year());
   dv = TPixel(doy_vector.data(),doy_vector.size());

   /*Some check*/
   if ( inBandsNumber != maskBandsNumber){
     throw std::invalid_argument("The number of bands between input and it's mask must be identical.\n\
input : "+std::to_string(inBandsNumber)+"\nmask : "+std::to_string(maskBandsNumber));
   }
   if (nbOutComp>inBandsNumber){
     throw std::invalid_argument("number of output components requested larger than input's number of component ("+std::to_string(inBandsNumber)+")");
   }

   inputImage->UpdateOutputInformation();
   mask->UpdateOutputInformation();
   pars.NumberOfInputComponents = inputImage->GetNumberOfComponentsPerPixel();
   pars.nbOutComp = nbOutComp;
   pars.dateVector = dv;
   auto extract = extractSortedIndicesWithMask_Functor(pars);
   m_ExtractFilter = extractSortedIndicesWithMask_Filter::New();
   m_ExtractFilter->SetFunctor(extract);
   m_ExtractFilter->SetInput(0,inputImage);
   m_ExtractFilter->SetInput(1,mask);
   m_ExtractFilter->SetNumberOfOutputBands(nbOutComp);
   SetParameterOutputImage("out", m_ExtractFilter->GetOutput());
   
  }
  extractSortedIndicesWithMask_Filter::Pointer m_ExtractFilter;
};
}//end namespace Wrapper
}//end namespace otb

OTB_APPLICATION_EXPORT(otb::Wrapper::extractSortedIndices)
