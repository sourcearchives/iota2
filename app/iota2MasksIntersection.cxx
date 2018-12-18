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
#include "itkNaryFunctorImageFilter.h"
#include "otbLabelImageToVectorDataFilter.h"

namespace otb
{
namespace Wrapper
{

template <typename TIn, typename TOut> 
class MasksIntersectionFunctor{

public:
  enum Convention{edg, div, nodata};

  MasksIntersectionFunctor()
    : m_InValue(0), m_OutValue(255), m_Conventions()
  {}

  ~MasksIntersectionFunctor(){}

  inline TOut operator()(const std::vector<TIn> & in) const
  {
    assert(in.size() == m_Conventions.size());

    for(unsigned int i = 0; i<in.size(); ++i)
      {
      // This is only because applications do not handle List of UInt images
      unsigned int  inValue = static_cast<TOut>(in[i][0]);

      switch(m_Conventions[i])
        {
        case edg:
          // [0] because TIn is supposed to be vector
          // In S2 mask, 1 means no data
          if(inValue == 1)
            {
            return m_OutValue;
            }
          break;
        case div:
          // In landsat X div files, odd value means no data
          if(inValue%2 == 1)
            {
            return m_OutValue;
            }
          break;
      case nodata:
          // In landsat X nodata files, even value means no data
          if(inValue%2 == 0)
            {
            return m_OutValue;
            }
          break;
        }
      }
    return m_InValue;
  }
    
  TOut m_InValue;
  TOut m_OutValue;
  std::vector<Convention> m_Conventions;
};

class iota2MasksIntersection: public Application
{
public:
  using Self = iota2MasksIntersection;
  using Superclass = Application;
  using Pointer = itk::SmartPointer<Self>;
  using ConstPointer = itk::SmartPointer<const Self>;

  itkNewMacro(Self);
  itkTypeMacro(iota2MasksIntersection, otb::Application);

  using IntersectionFunctorType = MasksIntersectionFunctor<FloatVectorImageType::PixelType,UInt8ImageType::PixelType>;
  using IntersectionFilterType = itk::NaryFunctorImageFilter<FloatVectorImageType,UInt8ImageType,IntersectionFunctorType>;
  using PolygonizeFilterType = otb::LabelImageToVectorDataFilter<UInt8ImageType>;

private:
  void DoInit() override
  {
    SetName("iota2MasksIntersection");
    SetDescription("Performs intersection of several input masks");

    // Documentation
    SetDocName("Masks intersection");
    SetDocLongDescription("This application performs intersection of several input masks from Landsat or Sentinel2 products. Output can be retrieved as a raster or vector file.");
    SetDocLimitations("None");
    SetDocAuthors("Julien Michel");

    AddDocTag(Tags::Filter);
    AddDocTag("MultiTemporal");
    
    AddParameter(ParameterType_InputImageList,  "edg",   "Sentinel2 edge masks (EDG files)");
    SetParameterDescription("edg","List of Sentinel2 EDG files (1 means no data)");
    MandatoryOff("edg");

    AddParameter(ParameterType_InputImageList,  "div",   "Landsat div masks (DIV files)");
    SetParameterDescription("div","List of Landsat DIV files (odd value means no data)");
    MandatoryOff("div");
    AddParameter(ParameterType_InputImageList,  "nodata",   "Landsat no data masks (NODATA files)");
    SetParameterDescription("nodata","List of Landsat NODATA files (even value means no data)");
    MandatoryOff("nodata");


    AddParameter(ParameterType_Choice,"mode","Output mode (vector or raster)");
    AddChoice("mode.raster", "Output a raster mask");
    SetParameterDescription("mode.raster","Raster output mode");
    AddChoice("mode.vector", "Output a vector mask");
    SetParameterDescription("mode.vector","Vector output mode. Note that this mode does not perform streaming: all input masks will be loaded into memory.");


    AddParameter(ParameterType_OutputImage,"mode.raster.out","Output mask as a raster");
    SetParameterDescription("mode.raster.out","Output raster file. Encoding should be integer.");
    SetDefaultOutputPixelType("mode.raster.out",ImagePixelType_uint8);
    AddParameter(ParameterType_Int,"mode.raster.inv","Value for pixel inside mask");
    SetDefaultParameterInt("mode.raster.inv",255);
    AddParameter(ParameterType_Int,"mode.raster.outv","Value for pixel outside mask");
    SetDefaultParameterInt("mode.raster.outv",0);

    AddParameter(ParameterType_OutputVectorData,"mode.vector.out","Output mask as a vector");
    SetParameterDescription("mode.vector.out","Output vector file.");

    AddParameter(ParameterType_Bool,"mode.vector.8conn","Use 8 connexity for vectorisation");
    SetParameterDescription("mode.vector.8conn","If enabled, 8 connexity will be used during vectorization.");

    AddParameter(ParameterType_String,"mode.vector.field","Name of the field associated with polygons");
    SetParameterDescription("mode.vector.field","The vectorization operation will create a field with an associated label (which is expected to be constant and equal to mode.raster.outv)");
    SetParameterString("mode.vector.field","DN");

    AddRAMParameter();
  }

  void DoUpdateParameters() override
  {


  }

  void DoExecute() override
  {  
    m_IntersectionFilter = IntersectionFilterType::New();

    FloatVectorImageListType::Pointer edgList = this->GetParameterImageList("edg");

    for(auto it = edgList->Begin(); it!= edgList->End();++it)
      {
      m_IntersectionFilter->PushBackInput(it.Get());
      m_IntersectionFilter->GetFunctor().m_Conventions.push_back(IntersectionFunctorType::Convention::edg);
      }

    FloatVectorImageListType::Pointer divList = this->GetParameterImageList("div");

    for(auto it = divList->Begin(); it!= divList->End();++it)
      {
      m_IntersectionFilter->PushBackInput(it.Get());
      m_IntersectionFilter->GetFunctor().m_Conventions.push_back(IntersectionFunctorType::Convention::div);
      }

    FloatVectorImageListType::Pointer nodataList = this->GetParameterImageList("nodata");

    for(auto it = nodataList->Begin(); it!= nodataList->End();++it)
      {
      m_IntersectionFilter->PushBackInput(it.Get());
      m_IntersectionFilter->GetFunctor().m_Conventions.push_back(IntersectionFunctorType::Convention::nodata);
      }


    
    m_IntersectionFilter->GetFunctor().m_InValue = GetParameterInt("mode.raster.inv");
    m_IntersectionFilter->GetFunctor().m_OutValue = GetParameterInt("mode.raster.outv");

    
    if(GetParameterString("mode") == "raster")
      {
      SetParameterOutputImage("mode.raster.out",m_IntersectionFilter->GetOutput());
      }
    else
      {
      m_PolygonizeFilter = PolygonizeFilterType::New();
      m_PolygonizeFilter->SetInput(m_IntersectionFilter->GetOutput());
      m_PolygonizeFilter->SetInputMask(m_IntersectionFilter->GetOutput());
      m_PolygonizeFilter->SetUse8Connected(IsParameterEnabled("mode.vector.8conn"));
      m_PolygonizeFilter->SetFieldName(GetParameterString("mode.vector.field"));
      SetParameterOutputVectorData("mode.vector.out",m_PolygonizeFilter->GetOutput());
      }

  }

  IntersectionFilterType::Pointer m_IntersectionFilter;
  PolygonizeFilterType::Pointer m_PolygonizeFilter;

};
} // end namespace Wrapper
} // end namespace otb

  OTB_APPLICATION_EXPORT(otb::Wrapper::iota2MasksIntersection)
