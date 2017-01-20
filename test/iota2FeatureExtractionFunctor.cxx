/*=========================================================================

  Program:   gapfilling
  Language:  C++

  Copyright (c) Jordi Inglada. All rights reserved.

  See LICENSE for details.

  This software is distributed WITHOUT ANY WARRANTY; without even
  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
  PURPOSE.  See the above copyright notices for more information.

=========================================================================*/
#include "itkMacro.h"
#include "iota2FeatureExtraction.h"
#include "itkVariableLengthVector.h"
int fexFunctor(int argc, char * argv[])
{
  using ValueType = float;
  using PixelType = itk::VariableLengthVector<ValueType>;
  constexpr auto cpd = size_t{4};
  constexpr auto ri = size_t{1};
  constexpr auto ni = size_t{2};
  constexpr auto si = size_t{3};
  constexpr auto nbd = size_t{2};
  constexpr auto nif = ValueType{1.0};
  constexpr auto ndv = ValueType{-10000};
  constexpr auto nic = size_t{cpd*nbd};

  bool copyInputBands = true;
  if(argc!=2)
    {
    std::cout << "Need one arg" << "\n";
    return EXIT_FAILURE;
    }
  if(std::stoi(argv[1]) == 0)
    {
    copyInputBands = false;
    }
  
  size_t outOffset = (copyInputBands?cpd:0);

  std::vector<ValueType> inVec{2,3,4,5,
      5,4,3,2};
  const auto ndvi1 = (inVec[ni-1]-inVec[ri-1])/(inVec[ni-1]+inVec[ri-1]);
  const auto ndvi2 = (inVec[ni+cpd-1]-inVec[ri+cpd-1])/
    (inVec[ni+cpd-1]+inVec[ri+cpd-1]);
  constexpr ValueType b2 = std::sqrt(ValueType{5*5+4*4+3*3+2*2});

  PixelType p(nic);
  for(size_t i=0; i<nic; i++)
    p[i] = inVec[i];
  auto func = iota2::FeatureExtractionFunctor<PixelType>(cpd,ri,ni,si,nif,ndv,
                                                         nic,copyInputBands);
  auto res = func(p);
  auto ndvi1_res = res[outOffset*nbd];
  auto ndvi2_res = res[outOffset*nbd+1];
  auto b2_res = res[outOffset*nbd+2*nbd+1];
  

  if(std::abs(ndvi1-ndvi1_res)>10e-5)
    {
    std::cout << "NDVI1 " << ndvi1 << "\t" << ndvi1_res << "\n";
    return EXIT_FAILURE;
    }

  if(std::abs(ndvi2-ndvi2_res)>10e-5)
    {
    std::cout << "NDVI2 "  << ndvi2 << "\t" << ndvi2_res << "\n";
    return EXIT_FAILURE;
    }

  if(std::abs(b2-b2_res)>10e-5)
    {
    std::cout  << "BRI2 " << b2 << "\t" << b2_res << "\n";
    return EXIT_FAILURE;
    }

  if(p[1]!=res[1] && copyInputBands)
    {
    std::cout << p[1] << "\t" << res[1] << "\n";
    return EXIT_FAILURE;
    }


  p[0] = ndv;
  res = func(p);
  ndvi1_res = res[outOffset*nbd];
  if(ndvi1_res != ndv)
    {
    std::cout << p[0] << "\t" << res[1] << " --> should be no data\n";
    return EXIT_FAILURE;
    }

  return EXIT_SUCCESS;
}
