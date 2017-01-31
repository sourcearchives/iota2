/*=========================================================================

  Program:   iota2
  Language:  C++

  Copyright (c) CESBIO. All rights reserved.

  See LICENSE for details.

  This software is distributed WITHOUT ANY WARRANTY; without even
  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
  PURPOSE.  See the above copyright notices for more information.

=========================================================================*/
#include <cstddef>
#include <cmath>
#include <limits>
#include <vector>
#include <algorithm>
#include <numeric>
#include "itkUnaryFunctorImageFilter.h"

namespace iota2
{
/** Unary functor image filter which produces a vector image with a
* number of bands different from the input images */
template <class TInputImage ,class TOutputImage, class TFunctor>
class ITK_EXPORT UnaryFunctorImageFilterWithNBands : 
    public itk::UnaryFunctorImageFilter< TInputImage, TOutputImage, TFunctor >
{
public:
  typedef UnaryFunctorImageFilterWithNBands Self;
  typedef itk::UnaryFunctorImageFilter< TInputImage, TOutputImage, 
                                        TFunctor > Superclass;
  typedef itk::SmartPointer<Self>       Pointer;
  typedef itk::SmartPointer<const Self> ConstPointer;

  /** Method for creation through the object factory. */
  itkNewMacro(Self);

  /** Macro defining the type*/
  itkTypeMacro(UnaryFunctorImageFilterWithNBands, SuperClass);
  
  /** Accessors for the number of bands*/
  itkSetMacro(NumberOfOutputBands, unsigned int);
  itkGetConstMacro(NumberOfOutputBands, unsigned int);
  
protected:
  UnaryFunctorImageFilterWithNBands() {}
  virtual ~UnaryFunctorImageFilterWithNBands() {}

  virtual void GenerateOutputInformation()
  {
    Superclass::GenerateOutputInformation();
    this->GetOutput()->SetNumberOfComponentsPerPixel( m_NumberOfOutputBands );
  }
private:
  UnaryFunctorImageFilterWithNBands(const Self &); //purposely not implemented
  void operator =(const Self&); //purposely not implemented

  unsigned int m_NumberOfOutputBands;


};

template <typename T>
constexpr T normalized_index(T refl, T refrefl, T epsilon=10e-6)
{
  return std::fabs(refl+refrefl)<epsilon?
                                 T{0}:(refl-refrefl)/(refl+refrefl);
}

template <typename PixelType>
class FeatureExtractionFunctor
{
public:
  using ValueType =   typename PixelType::ValueType;
  using VectorType = std::vector<ValueType>;

  struct Parameters {
    size_t ComponentsPerDate;
    size_t RedIndex;
    size_t NIRIndex;
    size_t SWIRIndex;
    bool RelativeReflectances{false};
    size_t ReferenceIndex; 
    bool RemoveDuplicates{true}; 
    ValueType NormalizedIndexFactor;
    ValueType NoDataValue;
    size_t NumberOfInputComponents;
    bool CopyInputBands;
  };
  FeatureExtractionFunctor() = default;
  FeatureExtractionFunctor(Parameters pars)
    : m_ComponentsPerDate{pars.ComponentsPerDate}, m_RedIndex{pars.RedIndex}, 
      m_NIRIndex{pars.NIRIndex}, m_SWIRIndex{pars.SWIRIndex}, 
      m_RelativeReflectances{pars.RelativeReflectances}, 
      m_ReferenceIndex{pars.ReferenceIndex}, 
      m_RemoveDuplicates{pars.RemoveDuplicates}, 
      m_NormalizedIndexFactor{pars.NormalizedIndexFactor},
      m_NoDataValue{pars.NoDataValue}, 
      m_NumberOfInputComponents{pars.NumberOfInputComponents}, 
      m_CopyInputBands{pars.CopyInputBands}
  {
    m_NumberOfDates = m_NumberOfInputComponents/m_ComponentsPerDate;
    auto numberOfOutputFeatures = m_NumberOfFeatures-
      ((m_RelativeReflectances&&m_RemoveDuplicates)?1:0);
    m_NumberOfOutputComponents = ( numberOfOutputFeatures + 
                                   (m_CopyInputBands?
                                    m_ComponentsPerDate:0))*m_NumberOfDates;
    auto max_index_band = std::max({m_RedIndex, m_NIRIndex, m_SWIRIndex});
    if(max_index_band > m_ComponentsPerDate) 
      throw std::domain_error("Band indices and components per date are not coherent.");
  };

  PixelType operator()(const PixelType& p)
  {
    if(p.GetSize()%m_ComponentsPerDate != 0)
      throw std::domain_error("Pixel size incoherent with number of components per date.");
    PixelType result(m_NumberOfOutputComponents);
    //use std vectors instead of pixels
    auto inVec = VectorType(p.GetDataPointer(), 
                            p.GetDataPointer()+p.GetSize());
    //copy the spectral bands
    auto outVec = VectorType(m_NumberOfOutputComponents);
    //copy the input reflectances
    if(m_CopyInputBands)
      {
      AddReflectances(inVec, outVec);
      }

    ComputeFeatures(inVec, outVec);
    
    //convert the result to a pixel
    for(size_t i=0; i<m_NumberOfOutputComponents; i++)
      result[i] = outVec[i];
    return result;
  }

  bool operator!=(FeatureExtractionFunctor<PixelType> f)
  {
    return m_ComponentsPerDate != f.m_ComponentsPerDate;
  }

  size_t GetNumberOfOutputComponents() const
  {
    return m_NumberOfOutputComponents;
  }

protected:
  void AddReflectances(const VectorType& inVec, VectorType& outVec)
  {
    if(!m_RelativeReflectances)
      {
      std::copy(inVec.cbegin(), inVec.cend(), outVec.begin());
      }
    else
      {
      auto inIt = inVec.cbegin();
      auto outIt = outVec.begin();
      while(inIt != inVec.cend())
        {
        (*outIt) = normalized_index(*inIt, *(inIt+m_ReferenceIndex-1));
        ++inIt;
        ++outIt;
        }
      }
  }

  void ComputeFeatures(const VectorType& inVec, VectorType& outVec)
  {
    size_t copyOffset = (m_CopyInputBands?m_NumberOfInputComponents:0);
    size_t date_counter{0};
    auto inIt = inVec.cbegin();
    while(inIt != inVec.cend())
      {
      //check for invalid values
      if(std::any_of(inIt, inIt+m_ComponentsPerDate,
                     [&](ValueType x)
                     { 
                     return std::fabs(x - m_NoDataValue)<0.1;
                     })) 
        {
        outVec[copyOffset+date_counter] = m_NoDataValue;
        outVec[copyOffset+m_NumberOfDates+date_counter] = m_NoDataValue;
        outVec[copyOffset+m_NumberOfDates*2+date_counter] = m_NoDataValue;
        }
      else
        {
        //compute the features
        auto red = *(inIt+m_RedIndex-1);
        auto nir = *(inIt+m_NIRIndex-1);
        auto swir = *(inIt+m_SWIRIndex-1);
        VectorType tmpVec(m_ComponentsPerDate);
        std::transform(inIt, inIt+m_ComponentsPerDate,tmpVec.begin(),
                       [](decltype(*inIt)x){ return x*x;});
        auto brightness = std::sqrt(std::accumulate(tmpVec.begin(), tmpVec.end(), 
                                                    ValueType{0}));
        //append the features
        size_t featureOffset{0};

        AddNormalizedIndexMaybe(nir, red, m_RedIndex, featureOffset, 
                                copyOffset, outVec, date_counter);
        AddNormalizedIndexMaybe(swir, nir, m_NIRIndex, featureOffset, 
                                copyOffset, outVec, date_counter);
        outVec[copyOffset+m_NumberOfDates*featureOffset+date_counter] = brightness;
        }
      //move to the next date
      std::advance(inIt, m_ComponentsPerDate);
      ++date_counter;
      }
  }

  void AddNormalizedIndexMaybe(ValueType refl, ValueType refrefl, 
                                   size_t refindex, size_t& featureOffset,
                                   size_t copyOffset, VectorType& outVec,
                                   size_t date_counter)
  {
    if(!m_RemoveDuplicates || m_ReferenceIndex != refindex)
      {
      outVec[copyOffset+m_NumberOfDates*featureOffset+date_counter] = 
        normalized_index(refl, refrefl) * m_NormalizedIndexFactor;
      ++featureOffset;
      }
  }

  size_t m_ComponentsPerDate;
  size_t m_RedIndex;
  size_t m_NIRIndex;
  size_t m_SWIRIndex;
  bool m_RelativeReflectances;
  size_t m_ReferenceIndex; //which reflectance is used as reference if
  //relative reflectances are used
  bool m_RemoveDuplicates; //If relative reflectances, NDVI or NDWI
  //may be redundant
  ValueType m_NormalizedIndexFactor;
  ValueType m_NoDataValue;
  size_t m_NumberOfInputComponents;
  bool m_CopyInputBands;
  size_t m_NumberOfOutputComponents;
  size_t m_NumberOfDates;
  static constexpr size_t m_NumberOfFeatures = 3;
};
} // end namespace iota2

  
  
  
  
  
  
