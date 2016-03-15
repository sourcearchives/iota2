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

  void GenerateOutputInformation()
  {
    Superclass::GenerateOutputInformation();
    this->GetOutput()->SetNumberOfComponentsPerPixel( m_NumberOfOutputBands );
  }
private:
  UnaryFunctorImageFilterWithNBands(const Self &); //purposely not implemented
  void operator =(const Self&); //purposely not implemented

  unsigned int m_NumberOfOutputBands;


};
template <typename PixelType>
class FeatureExtractionFunctor
{
public:
  using ValueType =   typename PixelType::ValueType;

  FeatureExtractionFunctor() = default;
  FeatureExtractionFunctor(size_t cpd, size_t ri, size_t ni, size_t si,
                           ValueType ndv, size_t nic)
    : m_ComponentsPerDate{cpd}, m_RedIndex{ri},
      m_NIRIndex{ni}, m_SWIRIndex{si}, m_NoDataValue{ndv}, 
      m_NumberOfInputComponents{nic}
  {
    m_NumberOfDates = m_NumberOfInputComponents/m_ComponentsPerDate;
    m_NumberOfOutputComponents = (m_NumberOfFeatures + 
                                  m_ComponentsPerDate)*m_NumberOfDates;
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
    auto inVec = std::vector<ValueType>(p.GetDataPointer(), 
                                        p.GetDataPointer()+p.GetSize());
    //copy the spectral bands
    auto outVec = std::vector<ValueType>(m_NumberOfOutputComponents);
    //copy the input reflectances
    std::copy(inVec.cbegin(), inVec.cend(), outVec.begin());

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
        outVec[m_NumberOfInputComponents+date_counter] = m_NoDataValue;
        outVec[m_NumberOfInputComponents+m_NumberOfDates+date_counter] = m_NoDataValue;
        outVec[m_NumberOfInputComponents+m_NumberOfDates*2+date_counter] = m_NoDataValue;
        }
      else
        {
        //copute the features
        auto red = *(inIt+m_RedIndex-1);
        auto nir = *(inIt+m_NIRIndex-1);
        auto swir = *(inIt+m_SWIRIndex-1);
        auto ndvi = (nir-red)/(nir+red+std::numeric_limits<ValueType>::epsilon());
        auto ndwi = (swir-nir)/(swir+nir+std::numeric_limits<ValueType>::epsilon());
        decltype(inVec) tmpVec(m_ComponentsPerDate);
        std::transform(inIt, inIt+m_ComponentsPerDate,tmpVec.begin(),
                       [](decltype(*inIt)x){ return x*x;});
        auto brightness = std::sqrt(std::accumulate(tmpVec.begin(), tmpVec.end(), 
                                                    ValueType{0}));
        //append the features
        outVec[m_NumberOfInputComponents+date_counter] = ndvi;
        outVec[m_NumberOfInputComponents+m_NumberOfDates+date_counter] = ndwi;
        outVec[m_NumberOfInputComponents+m_NumberOfDates*2+date_counter] = brightness;
        }
      //move to the next date
      std::advance(inIt, m_ComponentsPerDate);
      ++date_counter;
      }
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
  size_t m_ComponentsPerDate;
  size_t m_RedIndex;
  size_t m_NIRIndex;
  size_t m_SWIRIndex;
  ValueType m_NoDataValue;
  size_t m_NumberOfInputComponents;
  size_t m_NumberOfOutputComponents;
  size_t m_NumberOfDates;
  static constexpr size_t m_NumberOfFeatures = 3;
};
} // end namespace iota2

  
  
  
  
  
